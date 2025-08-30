import streamlit as st
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")
st.title("Family Structure Tree Visualiser")

uploaded_file = st.file_uploader("Upload an Excel File", type=["xlsx"])

if uploaded_file:
    try:
        excel = pd.ExcelFile(uploaded_file)
        sheet = st.selectbox("Select Sheet", excel.sheet_names)
        df = excel.parse(sheet)

        st.subheader("Input Data Preview")
        st.dataframe(df)

        required_cols = ["Entity Name", "Type", "Relationship", "Connected To"]
        if all(col in df.columns for col in required_cols):
            G = nx.DiGraph()

            for _, row in df.iterrows():
                entity = row["Entity Name"]
                entity_type = row["Type"]
                connected_to = row["Connected To"]
                relationship = row["Relationship"]

                G.add_node(entity, type=entity_type)
                G.add_node(connected_to)
                G.add_edge(entity, connected_to, relationship=relationship)

            st.subheader("Family Structure Diagram")
            fig, ax = plt.subplots(figsize=(12, 8))
            pos = nx.spring_layout(G, seed=42)
            nx.draw(G, pos, with_labels=True, node_color="lightblue", node_size=3000, font_size=10, edge_color="gray", ax=ax)
            edge_labels = nx.get_edge_attributes(G, 'relationship')
            nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_color="red", ax=ax)
            st.pyplot(fig)
        else:
            st.error("Excel sheet must include columns: Entity Name, Type, Relationship, Connected To")
    except Exception as e:
        st.error(f"Error processing file: {e}")
