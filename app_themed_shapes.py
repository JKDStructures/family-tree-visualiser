
import streamlit as st
import pandas as pd
from io import BytesIO
from graphviz import Digraph
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet

st.set_page_config(layout="wide")
st.title("🌈 Themed Family Structure Builder with Shapes")

if "entities" not in st.session_state:
    st.session_state.entities = []
if "relationships" not in st.session_state:
    st.session_state.relationships = []
if "custom_fields" not in st.session_state:
    st.session_state.custom_fields = []

# Diagram layout
st.sidebar.title("⚙️ Diagram Settings")
diagram_direction = st.sidebar.selectbox("Diagram Direction", ["Left to Right", "Top to Bottom", "Right to Left", "Bottom to Top"])
rankdir_map = {
    "Left to Right": "LR",
    "Top to Bottom": "TB",
    "Right to Left": "RL",
    "Bottom to Top": "BT"
}
rankdir = rankdir_map[diagram_direction]

# File import
st.sidebar.title("📥 Import CSVs")
entities_file = st.sidebar.file_uploader("Upload Entities CSV", type="csv")
relationships_file = st.sidebar.file_uploader("Upload Relationships CSV", type="csv")

if entities_file:
    df = pd.read_csv(entities_file)
    known = ["Entity Name", "Type", "Address", "TFN", "ABN"]
    st.session_state.entities = df.to_dict(orient="records")
    st.session_state.custom_fields = [c for c in df.columns if c not in known]

if relationships_file:
    st.session_state.relationships = pd.read_csv(relationships_file).to_dict(orient="records")

# Manage entities
st.subheader("1️⃣ Manage Entities")
if st.button("➕ Add New Entity"):
    base = {"Entity Name": "", "Type": "Individual", "Address": "", "TFN": "", "ABN": ""}
    for field in st.session_state.custom_fields:
        base[field] = ""
    st.session_state.entities.append(base)

for i, ent in enumerate(st.session_state.entities):
    with st.expander(f"{i+1}. {ent['Entity Name'] or 'New Entity'}"):
        ent["Entity Name"] = st.text_input("Entity Name", ent["Entity Name"], key=f"ename_{i}")
        ent["Type"] = st.selectbox("Type", ["Individual", "Company", "Trust", "SMSF"], index=["Individual", "Company", "Trust", "SMSF"].index(ent["Type"]), key=f"etype_{i}")
        ent["Address"] = st.text_input("Address", ent["Address"], key=f"addr_{i}")
        ent["TFN"] = st.text_input("TFN", ent["TFN"], key=f"tfn_{i}")
        ent["ABN"] = st.text_input("ABN", ent["ABN"], key=f"abn_{i}")
        for field in st.session_state.custom_fields:
            ent[field] = st.text_input(field, ent.get(field, ""), key=f"cust_{i}_{field}")
        if st.button("❌ Delete", key=f"del_ent_{i}"):
            st.session_state.entities.pop(i)
            st.experimental_rerun()

# Manage custom fields
with st.expander("➕ Manage Custom Fields"):
    new_field = st.text_input("Add Custom Field")
    if st.button("Add Field"):
        if new_field and new_field not in st.session_state.custom_fields:
            st.session_state.custom_fields.append(new_field)
            for ent in st.session_state.entities:
                ent[new_field] = ""
    if st.session_state.custom_fields:
        remove_field = st.selectbox("Delete Field", st.session_state.custom_fields)
        if st.button("Delete Field"):
            st.session_state.custom_fields.remove(remove_field)
            for ent in st.session_state.entities:
                if remove_field in ent:
                    del ent[remove_field]

# Relationships
if st.session_state.entities:
    st.subheader("2️⃣ Manage Relationships")
    if st.button("➕ Add New Relationship"):
        names = [e["Entity Name"] for e in st.session_state.entities]
        st.session_state.relationships.append({
            "From": names[0], "To": names[0], "Relationship": ""
        })

    for j, rel in enumerate(st.session_state.relationships):
        with st.expander(f"{j+1}. {rel['From']} → {rel['To']}"):
            names = [e["Entity Name"] for e in st.session_state.entities]
            rel["From"] = st.selectbox("From", names, index=names.index(rel["From"]) if rel["From"] in names else 0, key=f"from_{j}")
            rel["To"] = st.selectbox("To", names, index=names.index(rel["To"]) if rel["To"] in names else 0, key=f"to_{j}")
            rel["Relationship"] = st.text_input("Relationship", rel["Relationship"], key=f"rel_{j}")
            if st.button("❌ Delete", key=f"del_rel_{j}"):
                st.session_state.relationships.pop(j)
                st.experimental_rerun()

# Export
st.subheader("📤 Export")
c1, c2 = st.columns(2)
c1.download_button("⬇️ Entities CSV", pd.DataFrame(st.session_state.entities).to_csv(index=False), "entities_export.csv", "text/csv")
c2.download_button("⬇️ Relationships CSV", pd.DataFrame(st.session_state.relationships).to_csv(index=False), "relationships_export.csv", "text/csv")

if st.button("⬇️ Download PDF Report"):
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter)
    styles = getSampleStyleSheet()
    story = [Paragraph("Family Structure Export", styles["Title"]), Spacer(1, 12)]
    story.append(Paragraph("Entities:", styles["Heading2"]))
    for ent in st.session_state.entities:
        txt = ", ".join([f"{k}: {v}" for k, v in ent.items() if v])
        story.append(Paragraph(txt, styles["Normal"]))
        story.append(Spacer(1, 6))
    story.append(Spacer(1, 12))
    story.append(Paragraph("Relationships:", styles["Heading2"]))
    for r in st.session_state.relationships:
        story.append(Paragraph(f"{r['From']} → {r['To']} ({r['Relationship']})", styles["Normal"]))
        story.append(Spacer(1, 6))
    doc.build(story)
    st.download_button("Download PDF", data=buf.getvalue(), file_name="structure_report.pdf")

# Diagram
if st.session_state.entities:
    st.subheader("📊 Diagram")
    dot = Digraph()
    dot.attr(rankdir=rankdir, splines='ortho')  # Avoid intersections

    shape_map = {
        "Individual": ("ellipse", "deepskyblue"),
        "Trust": ("box", "navy"),
        "Company": ("diamond", "seagreen"),
        "SMSF": ("hexagon", "purple")
    }

    for ent in st.session_state.entities:
        label_lines = [f"{ent['Entity Name']}\nType: {ent['Type']}"]
        for field in ["Address", "TFN", "ABN"] + st.session_state.custom_fields:
            if ent.get(field):
                label_lines.append(f"{field}: {ent[field]}")
        shape, color = shape_map.get(ent["Type"], ("box", "gray"))
        dot.node(ent["Entity Name"], label="\n".join(label_lines), shape=shape, style='filled', color=color, fontcolor="white")

    for rel in st.session_state.relationships:
        dot.edge(rel["From"], rel["To"], label=rel["Relationship"], color='red', style='dashed')

    st.graphviz_chart(dot)
