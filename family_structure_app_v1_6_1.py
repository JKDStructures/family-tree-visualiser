
import streamlit as st
import pandas as pd
import graphviz
from io import BytesIO
from fpdf import FPDF
from PIL import Image

st.set_page_config(layout="wide")
st.title("🧬 Family / Group Structure Visualiser v1.6.1")

# Session state setup
if "entities" not in st.session_state:
    st.session_state.entities = []
if "relationships" not in st.session_state:
    st.session_state.relationships = []
if "custom_fields" not in st.session_state:
    st.session_state.custom_fields = []

# Title input
structure_title = st.text_input("Structure Title", "")

# Upload CSV section
with st.expander("📤 Upload CSV Data (Optional)", expanded=False):
    ent_file = st.file_uploader("Upload Entities CSV", type=["csv"], key="upload_ent")
    rel_file = st.file_uploader("Upload Relationships CSV", type=["csv"], key="upload_rel")

    if ent_file:
        df = pd.read_csv(ent_file)
        st.session_state.entities = df.to_dict("records")
    if rel_file:
        df = pd.read_csv(rel_file)
        st.session_state.relationships = df.to_dict("records")

# Custom field controls
with st.expander("➕ Manage Custom Fields"):
    for field in st.session_state.custom_fields:
        st.text(f"📌 {field}")
    new_field = st.text_input("Add a custom field")
    if st.button("Add Field") and new_field:
        if new_field not in st.session_state.custom_fields:
            st.session_state.custom_fields.append(new_field)
    del_field = st.selectbox("Delete a custom field", [""] + st.session_state.custom_fields)
    if st.button("Delete Field") and del_field:
        st.session_state.custom_fields.remove(del_field)

# Entity Entry
with st.expander("👤 Add/Edit Entities"):
    with st.form("entity_form", clear_on_submit=True):
        name = st.text_input("Entity Name", "")
        etype = st.selectbox("Entity Type", ["Individual", "Company", "Trust", "SMSF"])
        address = st.text_input("Address", "")
        tfn = st.text_input("TFN", "")
        abn = st.text_input("ABN", "")
        acn = st.text_input("ACN", "")
        custom_data = {field: st.text_input(field, key=field) for field in st.session_state.custom_fields}
        if st.form_submit_button("Add Entity") and name:
            entry = {"name": name, "type": etype, "address": address, "TFN": tfn, "ABN": abn, "ACN": acn}
            entry.update(custom_data)
            st.session_state.entities.append(entry)

# Display + delete entities
if st.session_state.entities:
    st.subheader("Entities")
    for i, ent in enumerate(st.session_state.entities):
        st.write(f"{i+1}. {ent}")
        if st.button(f"Delete Entity {i+1}", key=f"delent{i}"):
            st.session_state.entities.pop(i)
            st.experimental_rerun()

# Relationship entry
with st.expander("🔗 Add/Edit Relationships"):
    with st.form("relationship_form", clear_on_submit=True):
        from_ent = st.selectbox("From", [e["name"] for e in st.session_state.entities])
        to_ent = st.selectbox("To", [e["name"] for e in st.session_state.entities])
        relation = st.text_input("Relationship Type", "")
        if st.form_submit_button("Add Relationship") and from_ent and to_ent:
            st.session_state.relationships.append({"from": from_ent, "to": to_ent, "label": relation})

# Display + delete relationships
if st.session_state.relationships:
    st.subheader("Relationships")
    for i, rel in enumerate(st.session_state.relationships):
        st.write(f"{i+1}. {rel}")
        if st.button(f"Delete Relationship {i+1}", key=f"delrel{i}"):
            st.session_state.relationships.pop(i)
            st.experimental_rerun()

# Graph generation
if st.button("📈 Generate Structure Diagram"):
    dot = graphviz.Digraph(comment=structure_title)
    type_shapes = {"Individual": "ellipse", "Company": "box", "Trust": "parallelogram", "SMSF": "hexagon"}
    type_colors = {"Individual": "lightblue", "Company": "lightgreen", "Trust": "lightyellow", "SMSF": "lightpink"}

    for ent in st.session_state.entities:
        label = f"{ent['name']}\n{ent['type']}"
        label += f"\n{ent['address']}" if ent.get("address") else ""
        label += f"\nTFN: {ent['TFN']}" if ent.get("TFN") else ""
        label += f"\nABN: {ent['ABN']}" if ent.get("ABN") else ""
        label += f"\nACN: {ent['ACN']}" if ent.get("ACN") else ""
        for field in st.session_state.custom_fields:
            if ent.get(field):
                label += f"\n{field}: {ent[field]}"
        dot.node(ent['name'], label=label, shape=type_shapes.get(ent['type'], "box"), style="filled", fillcolor=type_colors.get(ent['type'], "white"))

    for rel in st.session_state.relationships:
        dot.edge(rel["from"], rel["to"], label=rel["label"])

    st.graphviz_chart(dot)

    # Export options
    if st.button("📸 Export PNG"):
        dot.render("/tmp/structure", format="png", cleanup=False)
        with open("/tmp/structure.png", "rb") as f:
            st.download_button("Download PNG", f, file_name="structure.png")

    if st.button("🧾 Export PDF"):
        dot.render("/tmp/structure", format="pdf", cleanup=False)
        with open("/tmp/structure.pdf", "rb") as f:
            st.download_button("Download PDF", f, file_name="structure.pdf")

# Export CSV
st.download_button("⬇️ Download Entities CSV", pd.DataFrame(st.session_state.entities).to_csv(index=False), file_name="entities.csv")
st.download_button("⬇️ Download Relationships CSV", pd.DataFrame(st.session_state.relationships).to_csv(index=False), file_name="relationships.csv")
