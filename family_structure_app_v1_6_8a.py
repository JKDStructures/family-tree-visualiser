
import streamlit as st
import pandas as pd
from graphviz import Digraph
import requests
import uuid

st.set_page_config(page_title="Family/Group Structure Visualiser", layout="wide")

# --------------------------
# Session State & Constants
# --------------------------
BASE_FIELDS = ["id", "name", "type", "address", "TFN", "ABN", "ACN"]
ENTITY_TYPES = ["Individual", "Company", "Trust", "SMSF", "Other"]
TYPE_STYLE = {
    "Individual": dict(shape="ellipse", fillcolor="#3b82f6", style="filled", fontcolor="white"),
    "Company":    dict(shape="box",     fillcolor="#10b981", style="filled", fontcolor="white"),
    "Trust":      dict(shape="triangle", fillcolor="#1f2937", style="filled", fontcolor="white"),
    "SMSF":       dict(shape="diamond", fillcolor="#7c3aed", style="filled", fontcolor="white"),
    "Other":      dict(shape="hexagon",     fillcolor="#9ca3af", style="filled", fontcolor="white"),
}

def _init_state():
    if "entities" not in st.session_state: st.session_state.entities = []  # list[dict]
    if "relationships" not in st.session_state: st.session_state.relationships = []  # list[dict]
    if "custom_fields" not in st.session_state: st.session_state.custom_fields = []  # list[str]
    if "title" not in st.session_state: st.session_state.title = "Family/Group Structure"
    if "rankdir" not in st.session_state: st.session_state.rankdir = "LR"
    if "api_url" not in st.session_state: st.session_state.api_url = st.secrets.get("GRAPHVIZ_API_URL", "")
    if "ent_del_idx" not in st.session_state: st.session_state.ent_del_idx = None
    if "rel_del_idx" not in st.session_state: st.session_state.rel_del_idx = None

_init_state()

# --------------------------
# Helpers
# --------------------------
def ensure_id(entity: dict) -> dict:
    if not entity.get("id"):
        entity["id"] = str(uuid.uuid4())
    return entity

def entities_df() -> pd.DataFrame:
    columns = BASE_FIELDS + [f for f in st.session_state.custom_fields if f not in BASE_FIELDS]
    rows = []
    for e in st.session_state.entities:
        row = {k: e.get(k, "") for k in columns}
        rows.append(row)
    if not rows:
        return pd.DataFrame(columns=columns)
    return pd.DataFrame(rows)

def relationships_df() -> pd.DataFrame:
    if not st.session_state.relationships:
        return pd.DataFrame(columns=["source_id", "target_id", "label"])
    return pd.DataFrame(st.session_state.relationships)

def name_by_id(eid: str) -> str:
    for e in st.session_state.entities:
        if e.get("id") == eid:
            return e.get("name", eid)
    return eid

def id_by_name(name: str) -> str:
    for e in st.session_state.entities:
        if e.get("name") == name:
            return e.get("id")
    return ""

def scrub_new_custom_fields_from_df(df: pd.DataFrame):
    for col in df.columns:
        if col not in BASE_FIELDS and col not in st.session_state.custom_fields:
            st.session_state.custom_fields.append(col)

# --------------------------
# Build Graphviz DOT
# --------------------------
def build_graph() -> Digraph:
g = Digraph("G", engine="dot")   # or "sfdp" if you want force layout
g.attr(
    rankdir=st.session_state.rankdir,
    splines="true",       # allow curved lines
    overlap="false",      # prevent overlaps
    labelloc="t",
    fontsize="20",
    label=f'<<font point-size="28"><b>{st.session_state.title}</b></font>>'
)



    individual_ids = [e["id"] for e in st.session_state.entities if e.get("type") == "Individual"]

    # Cluster for Individuals (border invisible)
    if individual_ids:
        with g.subgraph(name="cluster_individuals") as c:
            c.attr(style="invis")
            for e in st.session_state.entities:
                if e["id"] in individual_ids:
                    style = TYPE_STYLE.get(e.get("type", "Other"), TYPE_STYLE["Other"]).copy()
                    label_lines = [f"<b>{e.get('name','')}</b> ({e.get('type','')})"]
                    for fld in ["address","TFN","ABN","ACN"] + st.session_state.custom_fields:
                        val = e.get(fld, "")
                        if val: label_lines.append(f"{fld}: {val}")
                    label = "<" + "<br/>".join(label_lines) + ">"
                    c.node(e["id"], label=label, **style)

    # Non-individuals outside cluster
    for e in st.session_state.entities:
        if e["id"] in individual_ids:
            continue
        style = TYPE_STYLE.get(e.get("type", "Other"), TYPE_STYLE["Other"]).copy()
        label_lines = [f"<b>{e.get('name','')}</b> ({e.get('type','')})"]
        for fld in ["address","TFN","ABN","ACN"] + st.session_state.custom_fields:
            val = e.get(fld, "")
            if val: label_lines.append(f"{fld}: {val}")
        label = "<" + "<br/>".join(label_lines) + ">"
        g.node(e["id"], label=label, **style)

    # Edges with near-line labels
    for r in st.session_state.relationships:
       g.edge(
    r["source_id"], r["target_id"],
    label=r.get("label",""),
    labelfloat="true",
    fontsize="10",
    labeldistance="0.5"   # just above 0, keeps it close but avoids collisions
)

    return g

# --------------------------
# Remote Rendering
# --------------------------
def render_remote(dot_source: str, fmt: str):
    base = st.session_state.api_url.strip() or st.secrets.get("GRAPHVIZ_API_URL", "").strip()
    if not base:
        st.error("No Graphviz API URL set (Sidebar → Graphviz API URL). Or export DOT and render elsewhere.")
        return None
    try:
        url = base.rstrip("/") + "/render"
        resp = requests.post(url, json={"dot": dot_source, "format": fmt}, timeout=60)
        if resp.status_code == 200:
            return resp.content
        st.error(f"Remote render failed: HTTP {resp.status_code} - {resp.text[:200]}")
    except Exception as e:
        st.error(f"Remote render error: {e}")
    return None

# --------------------------
# Sidebar Controls
# --------------------------
with st.sidebar:
    st.header("Settings")
    st.text_input("Diagram Title", key="title")
    st.selectbox(
        "Layout Direction",
        options=["Left → Right","Top → Bottom"],
        index=0 if st.session_state.rankdir == "LR" else 1,
        key="rankdir_label"
    )
    st.text_input("Graphviz API URL", key="api_url", placeholder="https://<your-renderer>")
    st.caption("Tip: set GRAPHVIZ_API_URL in Streamlit Secrets for production.")
    st.session_state.rankdir = "LR" if st.session_state.rankdir_label.startswith("Left") else "TB"

st.title("🧬 Family / Group Structure Visualiser")

# --------------------------
# CSV Upload (Append or Replace)
# --------------------------
st.subheader("📥 Import CSV (Optional)")
up_col1, up_col2, up_col3 = st.columns([1,1,1])
with up_col1:
    ent_file = st.file_uploader("Entities CSV", type=["csv"], key="ent_csv")
with up_col2:
    rel_file = st.file_uploader("Relationships CSV", type=["csv"], key="rel_csv")
with up_col3:
    append_mode = st.toggle("Append to current data", value=False)

if ent_file:
    df_ent = pd.read_csv(ent_file)
    scrub_new_custom_fields_from_df(df_ent)
    if "id" not in df_ent.columns:
        df_ent["id"] = [str(uuid.uuid5(uuid.NAMESPACE_DNS, str(n))) for n in df_ent["name"].fillna("").astype(str)]
    new_entities = df_ent.fillna("").to_dict("records")
    if append_mode:
        existing_ids = {e["id"] for e in st.session_state.entities}
        for e in new_entities:
            if e["id"] not in existing_ids:
                st.session_state.entities.append(ensure_id(e))
    else:
        st.session_state.entities = [ensure_id(e) for e in new_entities]
    st.success(f"Loaded {len(new_entities)} entities.")

if rel_file:
    df_rel = pd.read_csv(rel_file)
    if "source_id" not in df_rel.columns and "from" in df_rel.columns:
        df_rel["source_id"] = df_rel["from"].apply(lambda n: id_by_name(str(n)))
    if "target_id" not in df_rel.columns and "to" in df_rel.columns:
        df_rel["target_id"] = df_rel["to"].apply(lambda n: id_by_name(str(n)))
    if "label" not in df_rel.columns:
        df_rel["label"] = ""
    new_rels = df_rel[["source_id","target_id","label"]].fillna("").to_dict("records")
    if append_mode:
        st.session_state.relationships.extend(new_rels)
    else:
        st.session_state.relationships = new_rels
    st.success(f"Loaded {len(new_rels)} relationships.")

# --------------------------
# Add Entity
# --------------------------
st.subheader("👤 Add Entity")
with st.form("add_entity_form", clear_on_submit=True):
    c1,c2,c3 = st.columns(3)
    with c1:
        e_name = st.text_input("Name")
        e_type = st.selectbox("Type", ENTITY_TYPES, index=0)
    with c2:
        e_address = st.text_input("Address")
        e_tfn = st.text_input("TFN")
    with c3:
        e_abn = st.text_input("ABN")
        e_acn = st.text_input("ACN")
    # custom fields
    custom_vals = {}
    for f in st.session_state.custom_fields:
        custom_vals[f] = st.text_input(f)
    if st.form_submit_button("Add Entity"):
        if not e_name:
            st.warning("Please provide a name.")
        else:
            ent = ensure_id(dict(name=e_name, type=e_type, address=e_address, TFN=e_tfn, ABN=e_abn, ACN=e_acn))
            ent.update({k:v for k,v in custom_vals.items()})
            st.session_state.entities.append(ent)
            st.success(f"Added entity {e_name}")

# --------------------------
# Manage Custom Fields
# --------------------------
with st.expander("⚙️ Custom Fields", expanded=False):
    cf1, cf2 = st.columns([2,1])
    with cf1:
        new_field = st.text_input("Add new custom field")
        if st.button("Add Field"):
            if new_field and new_field not in st.session_state.custom_fields and new_field not in BASE_FIELDS:
                st.session_state.custom_fields.append(new_field)
                st.success(f"Added custom field “{new_field}”.")
    with cf2:
        if st.session_state.custom_fields:
            del_field = st.selectbox("Remove field", [""] + st.session_state.custom_fields)
            if st.button("Delete Field") and del_field:
                st.session_state.custom_fields.remove(del_field)
                for e in st.session_state.entities:
                    e.pop(del_field, None)
                st.success(f"Removed field “{del_field}”.")

# --------------------------
# Entities (Edit/Delete with deferred delete)
# --------------------------
st.subheader("📋 Entities (Edit/Delete)")
if st.session_state.entities:
    for idx, e in enumerate(list(st.session_state.entities)):
        with st.expander(f"{e['name']} — {e['type']}", expanded=False):
            c1,c2,c3 = st.columns(3)
            with c1:
                new_name = st.text_input("Name", e.get("name",""), key=f"ent_name_{e['id']}")
                new_type = st.selectbox("Type", ENTITY_TYPES, index=ENTITY_TYPES.index(e.get("type","Other")), key=f"ent_type_{e['id']}")
            with c2:
                new_address = st.text_input("Address", e.get("address",""), key=f"ent_addr_{e['id']}")
                new_tfn = st.text_input("TFN", e.get("TFN",""), key=f"ent_tfn_{e['id']}")
            with c3:
                new_abn = st.text_input("ABN", e.get("ABN",""), key=f"ent_abn_{e['id']}")
                new_acn = st.text_input("ACN", e.get("ACN",""), key=f"ent_acn_{e['id']}")
            # custom fields inline
            new_custom = {}
            for f in st.session_state.custom_fields:
                new_custom[f] = st.text_input(f, e.get(f,""), key=f"ent_{f}_{e['id']}")

            uc1, uc2 = st.columns([1,1])
            with uc1:
                if st.button("Save Changes", key=f"save_ent_{e['id']}"):
                    e.update(dict(name=new_name, type=new_type, address=new_address, TFN=new_tfn, ABN=new_abn, ACN=new_acn))
                    e.update(new_custom)
                    st.success("Saved.")
            with uc2:
                if st.button("Delete Entity", key=f"del_ent_{e['id']}"):
                    st.session_state.ent_del_idx = idx  # defer actual deletion

    # perform entity delete after loop
    if st.session_state.ent_del_idx is not None:
        idx = st.session_state.ent_del_idx
        if 0 <= idx < len(st.session_state.entities):
            ent_id = st.session_state.entities[idx]["id"]
            st.session_state.relationships = [
                r for r in st.session_state.relationships
                if r.get("source_id") != ent_id and r.get("target_id") != ent_id
            ]
            st.session_state.entities.pop(idx)
        st.session_state.ent_del_idx = None
        st.rerun()
else:
    st.info("No entities yet. Add some above or import from CSV.")

# --------------------------
# Add Relationship
# --------------------------
st.subheader("🔗 Add Relationship")
if len(st.session_state.entities) < 2:
    st.caption("Add at least two entities to create relationships.")
else:
    with st.form("add_rel_form", clear_on_submit=True):
        names = [e["name"] for e in st.session_state.entities]
        s1, s2, s3 = st.columns(3)
        with s1:
            from_name = st.selectbox("From", names, key="rel_from_name")
        with s2:
            to_name = st.selectbox("To", names, key="rel_to_name")
        with s3:
            rel_label = st.text_input("Label (e.g., owns, trustee for)")
        if st.form_submit_button("Add Relationship"):
            src_id = id_by_name(from_name)
            tgt_id = id_by_name(to_name)
            if src_id and tgt_id and src_id != tgt_id:
                st.session_state.relationships.append(dict(source_id=src_id, target_id=tgt_id, label=rel_label))
                st.success("Relationship added.")
            else:
                st.warning("Invalid source/target.")

# --------------------------
# Relationships (Edit/Delete) with deferred delete
# --------------------------
st.subheader("🧷 Relationships (Edit/Delete)")

if st.session_state.relationships:
    names = [e["name"] for e in st.session_state.entities]

    for i, r in enumerate(list(st.session_state.relationships)):
        src_name = name_by_id(r.get("source_id", "")) or "(missing)"
        tgt_name = name_by_id(r.get("target_id", "")) or "(missing)"
        header = f"{src_name} → {tgt_name} — {r.get('label','')}"
        with st.expander(header, expanded=False):
            # preselect with tolerance to missing names
            try:
                idx_from = names.index(src_name)
            except ValueError:
                idx_from = 0 if names else 0
            try:
                idx_to = names.index(tgt_name)
            except ValueError:
                idx_to = 0 if names else 0

            rr1, rr2, rr3 = st.columns(3)
            with rr1:
                new_from_name = st.selectbox(
                    f"From #{i}",
                    names if names else ["(no entities)"],
                    index=min(idx_from, max(len(names)-1, 0)),
                    key=f"r_from_{i}"
                )
            with rr2:
                new_to_name = st.selectbox(
                    f"To #{i}",
                    names if names else ["(no entities)"],
                    index=min(idx_to, max(len(names)-1, 0)),
                    key=f"r_to_{i}"
                )
            with rr3:
                new_label = st.text_input("Label", r.get("label",""), key=f"r_label_{i}")

            rc1, rc2 = st.columns([1,1])
            with rc1:
                if st.button("Save Relationship", key=f"r_save_{i}"):
                    r["source_id"] = id_by_name(new_from_name) or r.get("source_id","")
                    r["target_id"] = id_by_name(new_to_name) or r.get("target_id","")
                    r["label"] = new_label
                    st.success("Saved relationship.")
            with rc2:
                if st.button("Delete Relationship", key=f"r_del_{i}"):
                    st.session_state.rel_del_idx = i  # defer delete

    # perform relationship delete after loop
    if st.session_state.rel_del_idx is not None:
        idx = st.session_state.rel_del_idx
        if 0 <= idx < len(st.session_state.relationships):
            st.session_state.relationships.pop(idx)
        st.session_state.rel_del_idx = None
        st.rerun()
else:
    st.caption("No relationships yet.")

# --------------------------
# Diagram & Exports
# --------------------------
st.subheader("🗺️ Structure Diagram")
graph = build_graph()
st.graphviz_chart(graph)

st.subheader("📤 Export")
ec1, ec2, ec3, ec4 = st.columns(4)
with ec1:
    if st.button("Export PNG"):
        data = render_remote(graph.source, "png")
        if data:
            st.download_button("Download PNG", data=data, file_name="structure.png", mime="image/png")
with ec2:
    if st.button("Export PDF"):
        data = render_remote(graph.source, "pdf")
        if data:
            st.download_button("Download PDF", data=data, file_name="structure.pdf", mime="application/pdf")
with ec3:
    if st.button("Export DOT"):
        st.download_button("Download DOT", data=graph.source, file_name="structure.dot", mime="text/vnd.graphviz")
with ec4:
    if st.button("Export CSVs"):
        e_csv = entities_df().to_csv(index=False).encode("utf-8")
        r_csv = relationships_df().to_csv(index=False).encode("utf-8")
        st.download_button("Entities CSV", e_csv, file_name="entities.csv", mime="text/csv")
        st.download_button("Relationships CSV", r_csv, file_name="relationships.csv", mime="text/csv")
