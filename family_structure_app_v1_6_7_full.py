
import streamlit as st
from graphviz import Digraph
import pandas as pd
import requests
import uuid

st.set_page_config(page_title="Family Structure Visualiser", layout="wide")

st.title("🏠 Family / Group Structure Visualiser")

# Store session state for entities and relationships
if "entities" not in st.session_state:
    st.session_state.entities = []
if "relationships" not in st.session_state:
    st.session_state.relationships = []
if "custom_fields" not in st.session_state:
    st.session_state.custom_fields = []
if "title" not in st.session_state:
    st.session_state.title = ""

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

# --- Manual input UI ---
with st.expander("➕ Add Entity"):
    with st.form("add_entity"):
        col1, col2, col3 = st.columns(3)
        with col1:
            name = st.text_input("Name")
            entity_type = st.selectbox("Type", ["Individual", "Company", "Trust", "SMSF", "Other"])
        with col2:
            address = st.text_input("Address")
            tfn = st.text_input("TFN")
        with col3:
            abn = st.text_input("ABN")
            acn = st.text_input("ACN")
        
        custom_values = {}
        for field in st.session_state.custom_fields:
            custom_values[field] = st.text_input(f"Custom - {field}")

        submitted = st.form_submit_button("Add Entity")
        if submitted and name:
            entity_id = str(uuid.uuid4())
            st.session_state.entities.append({
                "id": entity_id,
                "name": name,
                "type": entity_type,
                "address": address,
                "tfn": tfn,
                "abn": abn,
                "acn": acn,
                "custom_fields": custom_values
            })

with st.expander("🔗 Add Relationship"):
    with st.form("add_relationship"):
        if len(st.session_state.entities) < 2:
            st.info("Need at least 2 entities to define a relationship.")
        else:
            source = st.selectbox("From", [e["name"] for e in st.session_state.entities])
            target = st.selectbox("To", [e["name"] for e in st.session_state.entities])
            label = st.text_input("Label (e.g., owns, trustee for)")
            rel_submit = st.form_submit_button("Add Relationship")
            if rel_submit:
                st.session_state.relationships.append({
                    "from": source,
                    "to": target,
                    "label": label
                })

with st.expander("⚙️ Custom Fields"):
    with st.form("add_custom_field"):
        new_field = st.text_input("Field Name")
        add_field = st.form_submit_button("Add Field")
        if add_field and new_field and new_field not in st.session_state.custom_fields:
            st.session_state.custom_fields.append(new_field)

# --- Title Input ---
st.text_input("Structure Title", value=st.session_state.title, key="title")

# --- Build Graphviz dot source ---
dot = Digraph(comment="Family Structure", format='png')
dot.attr(rankdir='LR', bgcolor="white")

type_colors = {
    "Individual": "lightblue",
    "Company": "lightgreen",
    "Trust": "gold",
    "SMSF": "plum",
    "Other": "gray"
}

for entity in st.session_state.entities:
    label = f"<<b>{entity['name']}</b><br/>{entity['type']}"
    if entity["address"]: label += f"<br/>{entity['address']}"
    if entity["tfn"]: label += f"<br/>TFN: {entity['tfn']}"
    if entity["abn"]: label += f"<br/>ABN: {entity['abn']}"
    if entity["acn"]: label += f"<br/>ACN: {entity['acn']}"
    for key, val in entity["custom_fields"].items():
        if val: label += f"<br/>{key}: {val}"
    label += ">"

    dot.node(entity["name"], label=label, shape="ellipse", style="filled", fillcolor=type_colors.get(entity["type"], "white"))

for rel in st.session_state.relationships:
    dot.edge(rel["from"], rel["to"], label=rel["label"], fontsize="10")

st.graphviz_chart(dot)

# --- Export Buttons ---
st.subheader("📤 Export Options")
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("Export as PDF"):
        pdf_data = render_remote(dot.source, fmt="pdf")
        if pdf_data:
            st.download_button("⬇️ Download PDF", pdf_data, file_name="structure.pdf")
with col2:
    if st.button("Export as PNG"):
        png_data = render_remote(dot.source, fmt="png")
        if png_data:
            st.download_button("⬇️ Download PNG", png_data, file_name="structure.png")
with col3:
    if st.button("Export CSV"):
        df = pd.DataFrame(st.session_state.entities)
        st.download_button("⬇️ Download CSV", df.to_csv(index=False), file_name="entities.csv", mime="text/csv")
