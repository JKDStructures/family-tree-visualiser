
import requests

def render_remote(dot_source, fmt='pdf'):
    try:
        url = "https://graphviz-api.onrender.com/render"
        response = requests.post(url, json={"dot": dot_source, "format": fmt})
        if response.status_code == 200:
            return response.content
        else:
            st.error(f"Remote render failed: {response.status_code}")
    except Exception as e:
        st.error(f"Remote render error: {str(e)}")



import streamlit as st
import pandas as pd
import graphviz
from fpdf import FPDF
import base64
from io import BytesIO
import uuid

# Initialize session state
for key, default in {
    "entities": [],
    "relationships": [],
    "custom_fields": [],
    "title": "Family/Group Structure",
    "direction": "LR"
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

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

    grouped = {"Individual": []}
    for idx, ent in enumerate(st.session_state.entities):
        node_id = f"node_{idx}"
        color, shape = entity_color_shape(ent["type"])
        label = f"<<b>{ent['name']}</b><br/>{ent['type']}"
        for field in ["address", "TFN", "ABN", "ACN"] + st.session_state.custom_fields:
            if ent.get(field):
                label += f"<br/>{field}: {ent[field]}"
        label += ">"
        dot.node(node_id, label=label, style="filled", fillcolor=color, shape=shape)
        if ent["type"] == "Individual":
            grouped["Individual"].append(node_id)
    for rel in st.session_state.relationships:
        from_id = next((f"node_{i}" for i, e in enumerate(st.session_state.entities) if e["name"] == rel["from"]), None)
        to_id = next((f"node_{i}" for i, e in enumerate(st.session_state.entities) if e["name"] == rel["to"]), None)
        if from_id and to_id:
            dot.edge(from_id, to_id, label=rel["label"], fontsize="10")
    if grouped["Individual"]:
        with dot.subgraph(name="cluster_ind") as c:
            c.attr(style="invis")
            for nid in grouped["Individual"]:
                c.node(nid)
    return dot

def generate_pdf(dot, title):
    from graphviz import Source
    pdf_bytes = dot.pipe(format="pdf")
    return pdf_bytes

def generate_png(dot):
    return dot.pipe(format="png")

st.title("Family Structure Visualiser v1.6.4")
st.text_input("Structure Title", value=st.session_state.title, key="title")
st.radio("Diagram Direction", ["LR", "TB"], key="direction")

upload_mode = st.radio("Input Mode", ["Manual Input", "Upload CSV"])
if upload_mode == "Upload CSV":
    ent_csv = st.file_uploader("Upload Entities CSV", type="csv")
    rel_csv = st.file_uploader("Upload Relationships CSV", type="csv")
    if ent_csv and rel_csv:
        st.session_state.entities = pd.read_csv(ent_csv).to_dict("records")
        st.session_state.relationships = pd.read_csv(rel_csv).to_dict("records")
        st.success("Data loaded from CSV.")
else:
    with st.expander("Add Entity"):
        name = st.text_input("Name")
        etype = st.selectbox("Type", ["Individual", "Company", "Trust", "SMSF"])
        address = st.text_input("Address")
        TFN = st.text_input("TFN")
        ABN = st.text_input("ABN")
        ACN = st.text_input("ACN")
        custom_vals = {f: st.text_input(f"{f}") for f in st.session_state.custom_fields}
        if st.button("Add Entity"):
            ent = {"name": name, "type": etype, "address": address, "TFN": TFN, "ABN": ABN, "ACN": ACN}
            ent.update(custom_vals)
            st.session_state.entities.append(ent)
            st.success(f"{name} added")

    with st.expander("Add Relationship"):
        if st.session_state.entities:
            from_ = st.selectbox("From", [e["name"] for e in st.session_state.entities], key="from_ent")
            to_ = st.selectbox("To", [e["name"] for e in st.session_state.entities], key="to_ent")
            label = st.text_input("Relationship Label")
            if st.button("Add Relationship"):
                st.session_state.relationships.append({"from": from_, "to": to_, "label": label})
                st.success("Relationship added.")

    with st.expander("Custom Fields"):
        new_field = st.text_input("New Custom Field")
        if st.button("Add Field"):
            if new_field not in st.session_state.custom_fields:
                st.session_state.custom_fields.append(new_field)
                st.success(f"Field '{new_field}' added")

# Show added data with delete buttons
st.subheader("Entities")
for i, ent in enumerate(st.session_state.entities):
    with st.expander(f"{ent['name']} ({ent['type']})", expanded=False):
        edited = {}
        edited["name"] = st.text_input(f"Name {i}", ent["name"], key=f"ent_name_{i}")
        edited["type"] = st.selectbox(f"Type {i}", ["Individual", "Company", "Trust", "SMSF"], index=["Individual", "Company", "Trust", "SMSF"].index(ent["type"]), key=f"ent_type_{i}")
        edited["address"] = st.text_input(f"Address {i}", ent.get("address", ""), key=f"ent_address_{i}")
        edited["TFN"] = st.text_input(f"TFN {i}", ent.get("TFN", ""), key=f"ent_TFN_{i}")
        edited["ABN"] = st.text_input(f"ABN {i}", ent.get("ABN", ""), key=f"ent_ABN_{i}")
        edited["ACN"] = st.text_input(f"ACN {i}", ent.get("ACN", ""), key=f"ent_ACN_{i}")
        for field in st.session_state.custom_fields:
            edited[field] = st.text_input(f"{field} {i}", ent.get(field, ""), key=f"ent_cust_{field}_{i}")
        if st.button(f"Update Entity {i}"):
            st.session_state.entities[i] = edited
            st.success("Entity updated.")
        if st.button(f"Delete Entity {i}"):
            st.session_state.entities.pop(i)
            st.experimental_rerun()

st.subheader("Relationships")
for i, rel in enumerate(st.session_state.relationships):
    with st.expander(f"{rel['from']} ➝ {rel['to']} ({rel['label']})", expanded=False):
        new_rel = {}
        new_rel["from"] = st.selectbox(f"From {i}", [e["name"] for e in st.session_state.entities], index=[e["name"] for e in st.session_state.entities].index(rel["from"]), key=f"rel_from_{i}")
        new_rel["to"] = st.selectbox(f"To {i}", [e["name"] for e in st.session_state.entities], index=[e["name"] for e in st.session_state.entities].index(rel["to"]), key=f"rel_to_{i}")
        new_rel["label"] = st.text_input(f"Label {i}", rel["label"], key=f"rel_label_{i}")
        if st.button(f"Update Relationship {i}"):
            st.session_state.relationships[i] = new_rel
            st.success("Relationship updated.")
        if st.button(f"Delete Relationship {i}"):
            st.session_state.relationships.pop(i)
            st.experimental_rerun()

# Diagram
st.subheader("Diagram")
graph = render_graph()
st.graphviz_chart(graph)

# Export options
st.subheader("Export")
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("Export PDF"):
        b = generate_pdf(graph, st.session_state.title)
        b64 = base64.b64encode(b).decode()
        href = f'<a href="data:application/pdf;base64,{b64}" download="structure.pdf">Download PDF</a>'
        st.markdown(href, unsafe_allow_html=True)
with col2:
    if st.button("Export PNG"):
        b = generate_png(graph)
        b64 = base64.b64encode(b).decode()
        href = f'<a href="data:image/png;base64,{b64}" download="structure.png">Download PNG</a>'
        st.markdown(href, unsafe_allow_html=True)
with col3:
    if st.button("Export CSVs"):
        e_df = pd.DataFrame(st.session_state.entities)
        r_df = pd.DataFrame(st.session_state.relationships)
        e_csv = e_df.to_csv(index=False).encode()
        r_csv = r_df.to_csv(index=False).encode()
        st.download_button("Download Entities CSV", e_csv, "entities.csv", "text/csv")
        st.download_button("Download Relationships CSV", r_csv, "relationships.csv", "text/csv")
