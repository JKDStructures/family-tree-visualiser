
# Streamlit Family Structure Visualiser v1.4 (Graphviz based)
import streamlit as st
import pandas as pd
import graphviz
import base64
from io import BytesIO
from PIL import Image
from fpdf import FPDF

st.set_page_config(layout="wide", page_title="Family/Group Structure")

st.markdown("## 📊 Family/Group Structure")

# Title input
title = st.text_input("Structure Title", "Family/Group Structure")

# Upload or input entity data
uploaded_entities = st.file_uploader("Upload Entities CSV", type="csv")
uploaded_relationships = st.file_uploader("Upload Relationships CSV", type="csv")

if uploaded_entities and uploaded_relationships:
    entities_df = pd.read_csv(uploaded_entities)
    relationships_df = pd.read_csv(uploaded_relationships)

    # Create a map of entity types to styles
    type_styles = {
        "Individual": {"shape": "ellipse", "style": "filled", "fillcolor": "deepskyblue"},
        "Company": {"shape": "diamond", "style": "filled", "fillcolor": "seagreen"},
        "Trust": {"shape": "box", "style": "filled", "fillcolor": "navy", "fontcolor": "white"},
        "SMSF": {"shape": "hexagon", "style": "filled", "fillcolor": "purple", "fontcolor": "white"},
    }

    g = graphviz.Digraph("G", format="png")
    g.attr(rankdir="TB", size="10")

    # Add nodes
    for _, row in entities_df.iterrows():
        eid = str(row["ID"])
        label = f"{row['Name']}"
        if row['Type']:
            label += f"\nType: {row['Type']}"
        if row.get("Address"):
            label += f"\nAddress: {row['Address']}"
        if row.get("TFN"):
            label += f"\nTFN: {row['TFN']}"
        if row.get("ABN"):
            label += f"\nABN: {row['ABN']}"
        if row.get("ACN"):
            label += f"\nACN: {row['ACN']}"

        node_kwargs = type_styles.get(row['Type'], {"shape": "box"})
        g.node(eid, label=label, **node_kwargs)

    # Draw relationships
    for _, rel in relationships_df.iterrows():
        g.edge(str(rel["Source"]), str(rel["Target"]), label=rel["Relationship"])

    # Render Graph
    st.graphviz_chart(g)

    # Export functions
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

    # Download buttons
    png_data = export_png(g)
    st.download_button("📥 Download PNG", data=png_data, file_name="family_structure.png")

    pdf_data = export_pdf(png_data)
    st.download_button("📄 Download PDF", data=pdf_data, file_name="family_structure.pdf")
