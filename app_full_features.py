import streamlit as st
from graphviz import Digraph
import pandas as pd
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet

st.set_page_config(layout="wide")
st.title("🧩 Family Structure Builder")

if "entities" not in st.session_state:
    st.session_state.entities = []
if "relationships" not in st.session_state:
    st.session_state.relationships = []

# --- ENTITY CREATION ---
st.subheader("1️⃣ Add Entities")

with st.form("entity_form", clear_on_submit=True):
    cols = st.columns(3)
    name = cols[0].text_input("Entity Name")
    entity_type = cols[1].selectbox("Type", ["Individual", "Company", "Trust", "SMSF"])
    address = cols[2].text_input("Address")

    cols2 = st.columns(3)
    tfn = cols2[0].text_input("TFN")
    abn = cols2[1].text_input("ABN")
    shares = cols2[2].text_input("Shares")

    add_entity = st.form_submit_button("Add Entity")
    if add_entity and name:
        st.session_state.entities.append({
            "Entity Name": name,
            "Type": entity_type,
            "Address": address,
            "TFN": tfn,
            "ABN": abn,
            "Shares": shares
        })

# --- ENTITY TABLE WITH DELETE ---
if st.session_state.entities:
    st.subheader("📋 Current Entities")
    for i, entity in enumerate(st.session_state.entities):
        st.markdown(f"**{i+1}. {entity['Entity Name']}** ({entity['Type']})")
        st.text(f"Address: {entity['Address']} | TFN: {entity['TFN']} | ABN: {entity['ABN']} | Shares: {entity['Shares']}")
        if st.button(f"Delete Entity {i+1}", key=f"del_entity_{i}"):
            st.session_state.entities.pop(i)
            st.experimental_rerun()

# --- RELATIONSHIPS ---
if st.session_state.entities:
    st.subheader("2️⃣ Define Relationships")

    with st.form("relationship_form", clear_on_submit=True):
        from_entity = st.selectbox("From Entity", [e["Entity Name"] for e in st.session_state.entities])
        to_entity = st.selectbox("To Entity", [e["Entity Name"] for e in st.session_state.entities])
        relationship = st.text_input("Relationship (e.g. Trustee, Shareholder, Director)")

        rel_submit = st.form_submit_button("Add Relationship")
        if rel_submit and from_entity and to_entity and relationship:
            st.session_state.relationships.append({
                "From": from_entity,
                "To": to_entity,
                "Relationship": relationship
            })

# --- RELATIONSHIP TABLE WITH DELETE ---
if st.session_state.relationships:
    st.subheader("🔗 Current Relationships")
    for i, rel in enumerate(st.session_state.relationships):
        st.text(f"{i+1}. {rel['From']} → {rel['To']} ({rel['Relationship']})")
        if st.button(f"Delete Relationship {i+1}", key=f"del_rel_{i}"):
            st.session_state.relationships.pop(i)
            st.experimental_rerun()

# --- EXPORT ---
st.subheader("📤 Export Data")

col1, col2 = st.columns(2)

with col1:
    if st.button("Download CSVs"):
        ent_df = pd.DataFrame(st.session_state.entities)
        rel_df = pd.DataFrame(st.session_state.relationships)

        ent_df.to_csv("entities_export.csv", index=False)
        rel_df.to_csv("relationships_export.csv", index=False)
        st.success("CSV files saved as entities_export.csv and relationships_export.csv")

with col2:
    if st.button("Download PDF"):
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

# --- GRAPHVIZ DIAGRAM ---
if st.session_state.entities:
    st.subheader("📊 Visual Diagram")

    dot = Digraph()
    dot.attr(rankdir='LR', splines='curved')

    for ent in st.session_state.entities:
        label = f"{ent['Entity Name']}\nType: {ent['Type']}"
        if ent['Address']:
            label += f"\nAddr: {ent['Address']}"
        if ent['TFN']:
            label += f"\nTFN: {ent['TFN']}"
        if ent['ABN']:
            label += f"\nABN: {ent['ABN']}"
        if ent['Shares']:
            label += f"\nShares: {ent['Shares']}"

        dot.node(ent['Entity Name'], label=label, shape='box', style='filled', color='navy', fontcolor='white')

    for rel in st.session_state.relationships:
        dot.edge(rel['From'], rel['To'], label=rel['Relationship'], color='red', style='dashed')

    st.graphviz_chart(dot)
