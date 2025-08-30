
import streamlit as st
import pandas as pd
import graphviz
from io import BytesIO
from PIL import Image
from fpdf import FPDF

st.set_page_config(layout="wide", page_title="Family Structure Visualiser v1.5")

st.title("📘 Family / Group Structure Visualiser")
title = st.text_input("Structure Title", "Family Group Structure")

# --- SESSION STATE INIT ---
if "entities" not in st.session_state:
    st.session_state.entities = pd.DataFrame(columns=["ID", "Name", "Type", "Address", "TFN", "ABN", "ACN"])
if "relationships" not in st.session_state:
    st.session_state.relationships = pd.DataFrame(columns=["Source", "Target", "Relationship"])

# --- FILE UPLOADS ---
st.subheader("📁 Upload CSVs (Optional)")
col1, col2 = st.columns(2)
with col1:
    uploaded_entities = st.file_uploader("Upload Entities CSV", type="csv", key="ent_csv")
    if uploaded_entities:
        st.session_state.entities = pd.read_csv(uploaded_entities)
with col2:
    uploaded_relationships = st.file_uploader("Upload Relationships CSV", type="csv", key="rel_csv")
    if uploaded_relationships:
        st.session_state.relationships = pd.read_csv(uploaded_relationships)

# --- ENTITY FORM ---
st.subheader("👤 Add New Entity")
with st.form("entity_form"):
    col1, col2, col3 = st.columns(3)
    with col1:
        name = st.text_input("Name")
        type_ = st.selectbox("Type", ["Individual", "Company", "Trust", "SMSF"])
    with col2:
        address = st.text_input("Address")
        tfn = st.text_input("TFN")
    with col3:
        abn = st.text_input("ABN")
        acn = st.text_input("ACN")
    submitted = st.form_submit_button("Add Entity")
    if submitted and name:
        new_id = str(len(st.session_state.entities) + 1)
        st.session_state.entities.loc[len(st.session_state.entities)] = [new_id, name, type_, address, tfn, abn, acn]
        st.success(f"Added entity: {name}")

# --- ENTITY TABLE ---
st.subheader("📋 Current Entities")
st.dataframe(st.session_state.entities, use_container_width=True)

# --- RELATIONSHIP FORM ---
st.subheader("🔗 Add New Relationship")
with st.form("rel_form"):
    rel_col1, rel_col2, rel_col3 = st.columns(3)
    with rel_col1:
        source = st.selectbox("Source", st.session_state.entities["ID"] + " - " + st.session_state.entities["Name"])
    with rel_col2:
        target = st.selectbox("Target", st.session_state.entities["ID"] + " - " + st.session_state.entities["Name"])
    with rel_col3:
        rel_type = st.text_input("Relationship Label")
    rel_submit = st.form_submit_button("Add Relationship")
    if rel_submit:
        st.session_state.relationships.loc[len(st.session_state.relationships)] = [
            source.split(" - ")[0], target.split(" - ")[0], rel_type]
        st.success("Relationship added.")

# --- RELATIONSHIP TABLE ---
st.subheader("🔎 Current Relationships")
st.dataframe(st.session_state.relationships, use_container_width=True)

# --- GRAPH GENERATION ---
st.subheader("📈 Visualisation")
g = graphviz.Digraph("G", format="png")
g.attr(rankdir="TB")

type_styles = {
    "Individual": {"shape": "ellipse", "style": "filled", "fillcolor": "deepskyblue"},
    "Company": {"shape": "diamond", "style": "filled", "fillcolor": "seagreen"},
    "Trust": {"shape": "box", "style": "filled", "fillcolor": "navy", "fontcolor": "white"},
    "SMSF": {"shape": "hexagon", "style": "filled", "fillcolor": "purple", "fontcolor": "white"},
}

for _, row in st.session_state.entities.iterrows():
    eid = str(row["ID"])
    label = f"{row['Name']}\n{row['Type']}"
    for field in ["Address", "TFN", "ABN", "ACN"]:
        if pd.notna(row[field]) and row[field] != "":
            label += f"\n{field}: {row[field]}"
    g.node(eid, label=label, **type_styles.get(row["Type"], {"shape": "box"}))

for _, rel in st.session_state.relationships.iterrows():
    g.edge(str(rel["Source"]), str(rel["Target"]), label=rel["Relationship"])

st.graphviz_chart(g)

# --- EXPORTS ---
def export_png(graph):
    return graph.pipe(format="png")

def export_pdf(png_bytes):
    img = Image.open(BytesIO(png_bytes))
    pdf = FPDF(orientation="L", unit="pt", format=[img.width, img.height])
    pdf.add_page()
    img_io = BytesIO()
    img.save(img_io, format="PNG")
    img_io.seek(0)
    pdf.image(img_io, x=0, y=0)
    pdf_bytes = BytesIO()
    pdf.output(pdf_bytes)
    pdf_bytes.seek(0)
    return pdf_bytes.read()

png_data = export_png(g)
st.download_button("📥 Download PNG", data=png_data, file_name="family_structure.png")

pdf_data = export_pdf(png_data)
st.download_button("📄 Download PDF", data=pdf_data, file_name="family_structure.pdf")

st.download_button("⬇️ Download Entities CSV", st.session_state.entities.to_csv(index=False), "entities_export.csv")
st.download_button("⬇️ Download Relationships CSV", st.session_state.relationships.to_csv(index=False), "relationships_export.csv")
