import streamlit as st
from graphviz import Digraph

st.set_page_config(layout="wide")
st.title("Interactive Family Structure Builder")

# Initialize session state to store the entity relationships
if "relationships" not in st.session_state:
    st.session_state.relationships = []

# Display current structure table
if st.session_state.relationships:
    st.subheader("Current Structure Entries")
    st.table(st.session_state.relationships)

st.subheader("Add New Relationship")

with st.form("add_relationship_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        entity = st.text_input("Entity Name", "")
        entity_type = st.selectbox("Entity Type", ["Individual", "Company", "Trust", "SMSF"])
        tfn = st.text_input("TFN", "")
        abn = st.text_input("ABN", "")
    with col2:
        address = st.text_input("Address", "")
        shares = st.text_input("Shares", "")
        relationship = st.text_input("Relationship (e.g. Trustee, Shareholder)", "")
        connected_to = st.text_input("Connected To", "")

    submitted = st.form_submit_button("Add to Structure")
    if submitted:
        st.session_state.relationships.append({
            "Entity Name": entity,
            "Type": entity_type,
            "TFN": tfn,
            "ABN": abn,
            "Address": address,
            "Shares": shares,
            "Relationship": relationship,
            "Connected To": connected_to
        })

# Display graph
if st.session_state.relationships:
    st.subheader("Family Structure Diagram")

    dot = Digraph()
    dot.attr(rankdir='LR', splines='curved')

    for row in st.session_state.relationships:
        entity = row["Entity Name"]
        connected = row["Connected To"]
        rel = row["Relationship"]

        # Build label
        details = [f"{entity}", f"Type: {row['Type']}"]
        if row["TFN"]:
            details.append(f"TFN: {row['TFN']}")
        if row["ABN"]:
            details.append(f"ABN: {row['ABN']}")
        if row["Address"]:
            details.append(f"Addr: {row['Address']}")
        if row["Shares"]:
            details.append(f"Shares: {row['Shares']}")

        label = "\n".join(details)
        dot.node(entity, label=label, shape='box', style='filled', color='navy', fontcolor='white')

        if connected and not dot.node(connected):
            dot.node(connected, shape='box', style='filled', color='navy', fontcolor='white')

        dot.edge(entity, connected, label=rel, color='red', style='dashed')

    st.graphviz_chart(dot)
