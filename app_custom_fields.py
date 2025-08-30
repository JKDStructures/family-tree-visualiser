import streamlit as st
import pandas as pd
from io import BytesIO
from graphviz import Digraph
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet

st.set_page_config(layout="wide")
st.title("🛠️ Customisable Family Structure Builder")

if "entities" not in st.session_state:
    st.session_state.entities = []
if "relationships" not in st.session_state:
    st.session_state.relationships = []
if "custom_fields" not in st.session_state:
    st.session_state.custom_fields = []

# Sidebar options
st.sidebar.title("⚙️ Diagram Settings")
diagram_direction = st.sidebar.selectbox("Diagram Direction", ["Left to Right (LR)", "Top to Bottom (TB)", "Right to Left (RL)", "Bottom to Top (BT)"])
rankdir = {"Left to Right (LR)": "LR", "Top to Bottom (TB)": "TB", "Right to Left (RL)": "RL", "Bottom to Top (BT)": "BT"}[diagram_direction]

# CSV Import
st.sidebar.title("📥 Import CSVs")
entities_file = st.sidebar.file_uploader("Upload Entities CSV", type="csv")
relationships_file = st.sidebar.file_uploader("Upload Relationships CSV", type="csv")

if entities_file:
    df = pd.read_csv(entities_file)
    known_fields = ["Entity Name", "Type", "Address", "TFN", "ABN"]
    st.session_state.entities = df.to_dict(orient="records")
    st.session_state.custom_fields = [col for col in df.columns if col not in known_fields]

if relationships_file:
    st.session_state.relationships = pd.read_csv(relationships_file).to_dict(orient="records")

# Entity Entry
st.subheader("1️⃣ Manage Entities")
if st.button("➕ Add New Entity"):
    base = {"Entity Name": "", "Type": "Individual", "Address": "", "TFN": "", "ABN": ""}
    for field in st.session_state.custom_fields:
        base[field] = ""
    st.session_state.entities.append(base)

for i, ent in enumerate(st.session_state.entities):
    with st.expander(f"{i+1}. {ent['Entity Name'] or 'New Entity'}"):
        ent["Entity Name"] = st.text_input("Entity Name", value=ent["Entity Name"], key=f"ename_{i}")
        ent["Type"] = st.selectbox("Type", ["Individual", "Company", "Trust", "SMSF"], index=["Individual", "Company", "Trust", "SMSF"].index(ent["Type"]), key=f"etype_{i}")
        ent["Address"] = st.text_input("Address", value=ent["Address"], key=f"addr_{i}")
        ent["TFN"] = st.text_input("TFN", value=ent["TFN"], key=f"tfn_{i}")
        ent["ABN"] = st.text_input("ABN", value=ent["ABN"], key=f"abn_{i}")
        for field in st.session_state.custom_fields:
            ent[field] = st.text_input(field, value=ent.get(field, ""), key=f"custom_{field}_{i}")
        if st.button("❌ Delete", key=f"del_entity_{i}"):
            st.session_state.entities.pop(i)
            st.experimental_rerun()

# Add custom field
with st.expander("➕ Add Custom Field to Entities"):
    new_field = st.text_input("Custom Field Name")
    if st.button("Add Custom Field"):
        if new_field and new_field not in st.session_state.custom_fields:
            st.session_state.custom_fields.append(new_field)
            for ent in st.session_state.entities:
                ent[new_field] = ""

# Relationship Entry
if st.session_state.entities:
    st.subheader("2️⃣ Manage Relationships")
    if st.button("➕ Add New Relationship"):
        st.session_state.relationships.append({
            "From": st.session_state.entities[0]["Entity Name"],
            "To": st.session_state.entities[0]["Entity Name"],
            "Relationship": ""
        })

    for j, rel in enumerate(st.session_state.relationships):
        with st.expander(f"{j+1}. {rel['From']} → {rel['To']}"):
            rel["From"] = st.selectbox("From", [e["Entity Name"] for e in st.session_state.entities], index=[e["Entity Name"] for e in st.session_state.entities].index(rel["From"]) if rel["From"] in [e["Entity Name"] for e in st.session_state.entities] else 0, key=f"from_{j}")
            rel["To"] = st.selectbox("To", [e["Entity Name"] for e in st.session_state.entities], index=[e["Entity Name"] for e in st.session_state.entities].index(rel["To"]) if rel["To"] in [e["Entity Name"] for e in st.session_state.entities] else 0, key=f"to_{j}")
            rel["Relationship"] = st.text_input("Relationship", value=rel["Relationship"], key=f"rel_{j}")
            if st.button("❌ Delete", key=f"del_rel_{j}"):
                st.session_state.relationships.pop(j)
                st.experimental_rerun()

# Export options
st.subheader("📤 Export")
col1, col2 = st.columns(2)
with col1:
    st.download_button("⬇️ Download Entities CSV", pd.DataFrame(st.session_state.entities).to_csv(index=False), "entities_export.csv", "text/csv")
with col2:
    st.download_button("⬇️ Download Relationships CSV", pd.DataFrame(st.session_state.relationships).to_csv(index=False), "relationships_export.csv", "text/csv")

if st.button("⬇️ Download PDF Report"):
    pdf_buffer = BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = [Paragraph("Family Structure Export", styles["Title"]), Spacer(1, 12)]

    story.append(Paragraph("Entities:", styles["Heading2"]))
    for ent in st.session_state.entities:
        line = ", ".join([f"{k}: {v}" for k, v in ent.items() if v])
        story.append(Paragraph(line, styles["Normal"]))
        story.append(Spacer(1, 6))

    story.append(Spacer(1, 12))
    story.append(Paragraph("Relationships:", styles["Heading2"]))
    for rel in st.session_state.relationships:
        story.append(Paragraph(f"{rel['From']} → {rel['To']} ({rel['Relationship']})", styles["Normal"]))
        story.append(Spacer(1, 6))

    doc.build(story)
    st.download_button("Download PDF Report", data=pdf_buffer.getvalue(), file_name="family_structure_export.pdf")

# Graphviz diagram
if st.session_state.entities:
    st.subheader("📊 Diagram")
    dot = Digraph()
    dot.attr(rankdir=rankdir, splines='curved')

    for ent in st.session_state.entities:
        lines = [f"{ent['Entity Name']}\nType: {ent['Type']}"]
        for field in ["Address", "TFN", "ABN"] + st.session_state.custom_fields:
            if ent.get(field):
                lines.append(f"{field}: {ent[field]}")
        dot.node(ent["Entity Name"], label="\n".join(lines), shape='box', style='filled', color='navy', fontcolor='white')

    for rel in st.session_state.relationships:
        dot.edge(rel["From"], rel["To"], label=rel["Relationship"], color='red', style='dashed')

    st.graphviz_chart(dot)
