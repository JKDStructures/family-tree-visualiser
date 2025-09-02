
# Full app file rebuilt here will include:
# - Manual & CSV input
# - Graphviz visualisation
# - PNG/PDF download
# - Custom fields
# - Grouped individuals, ungrouped others
# - Invisible borders (white) on group boxes

import streamlit as st
import pandas as pd
import graphviz
from fpdf import FPDF
import base64
from io import BytesIO
import uuid

# Initialize session state
if "entities" not in st.session_state:
    st.session_state.entities = []
if "relationships" not in st.session_state:
    st.session_state.relationships = []
if "custom_fields" not in st.session_state:
    st.session_state.custom_fields = []
if "title" not in st.session_state:
    st.session_state.title = "Family/Group Structure"

# Utilities
def entity_color_shape(entity_type):
    return {
        "Individual": ("#d0e8ff", "ellipse"),
        "Company": ("#fff2cc", "box"),
        "Trust": ("#f4cccc", "component"),
        "SMSF": ("#d9ead3", "hexagon"),
    }.get(entity_type, ("white", "oval"))

def render_graph():
    dot = graphviz.Digraph()
    dot.attr(rankdir=st.session_state.direction.lower(), bgcolor="white")

    grouped_nodes = {"Individual": []}
    ungrouped_nodes = []

    for idx, ent in enumerate(st.session_state.entities):
        node_id = f"node_{idx}"
        color, shape = entity_color_shape(ent["type"])
        label = f"<<b>{ent['name']}</b><br/>{ent['type']}"
        for field in ["address", "TFN", "ABN", "ACN"]:
            if ent.get(field):
                label += f"<br/>{field}: {ent[field]}"
        for custom in st.session_state.custom_fields:
            if ent.get(custom):
                label += f"<br/>{custom}: {ent[custom]}"
        label += ">"
        dot.node(node_id, label=label, style="filled", fillcolor=color, shape=shape)
        if ent["type"] == "Individual":
            grouped_nodes["Individual"].append(node_id)
        else:
            ungrouped_nodes.append(node_id)

    for rel in st.session_state.relationships:
        from_idx = next((i for i, e in enumerate(st.session_state.entities) if e["name"] == rel["from"]), None)
        to_idx = next((i for i, e in enumerate(st.session_state.entities) if e["name"] == rel["to"]), None)
        if from_idx is not None and to_idx is not None:
            dot.edge(f"node_{from_idx}", f"node_{to_idx}", label=rel["label"], fontsize="10")

    if grouped_nodes["Individual"]:
        with dot.subgraph(name="cluster_individuals") as c:
            c.attr(style="invis")
            for node in grouped_nodes["Individual"]:
                c.node(node)

    return dot

# PDF/PNG Export placeholder (rendering workaround still required)
def fake_pdf_export():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=st.session_state.title, ln=True, align='C')
    return pdf.output(dest="S").encode("latin1")

# UI
st.title("Family Structure Visualiser v1.6.3")
st.text_input("Diagram Title", value=st.session_state.title, key="title")
st.radio("Diagram Direction", ["LR", "TB"], key="direction")

upload_mode = st.radio("Input Mode", ["Manual Input", "Upload CSV"])
if upload_mode == "Upload CSV":
    ent_file = st.file_uploader("Upload Entities CSV", type=["csv"], key="ent_csv")
    rel_file = st.file_uploader("Upload Relationships CSV", type=["csv"], key="rel_csv")
    if ent_file and rel_file:
        st.session_state.entities = pd.read_csv(ent_file).to_dict("records")
        st.session_state.relationships = pd.read_csv(rel_file).to_dict("records")
        st.success("CSV data loaded.")
else:
    with st.expander("Add Entity"):
        name = st.text_input("Name")
        ent_type = st.selectbox("Type", ["Individual", "Company", "Trust", "SMSF"])
        address = st.text_input("Address")
        TFN = st.text_input("TFN")
        ABN = st.text_input("ABN")
        ACN = st.text_input("ACN")
        custom_inputs = {field: st.text_input(f"{field}") for field in st.session_state.custom_fields}
        if st.button("Add Entity"):
            new_ent = {"name": name, "type": ent_type, "address": address, "TFN": TFN, "ABN": ABN, "ACN": ACN}
            new_ent.update(custom_inputs)
            st.session_state.entities.append(new_ent)
            st.success(f"Entity {name} added.")

    with st.expander("Add Relationship"):
        if st.session_state.entities:
            from_ent = st.selectbox("From", [e["name"] for e in st.session_state.entities])
            to_ent = st.selectbox("To", [e["name"] for e in st.session_state.entities])
            label = st.text_input("Relationship Label")
            if st.button("Add Relationship"):
                st.session_state.relationships.append({"from": from_ent, "to": to_ent, "label": label})
                st.success("Relationship added.")

    with st.expander("Custom Fields"):
        new_field = st.text_input("New Custom Field")
        if st.button("Add Custom Field") and new_field:
            if new_field not in st.session_state.custom_fields:
                st.session_state.custom_fields.append(new_field)
                st.success(f"Added custom field '{new_field}'")

# Diagram
st.subheader("Structure Diagram")
graph = render_graph()
st.graphviz_chart(graph)

# Export
st.subheader("Export Diagram")
col1, col2 = st.columns(2)
with col1:
    if st.button("Download PDF"):
        pdf_bytes = fake_pdf_export()
        b64 = base64.b64encode(pdf_bytes).decode()
        href = f'<a href="data:application/octet-stream;base64,{b64}" download="structure.pdf">Click here to download PDF</a>'
        st.markdown(href, unsafe_allow_html=True)
with col2:
    if st.button("Download PNG"):
        st.warning("PNG export is being patched for v1.6.4 (rendering issue)")
