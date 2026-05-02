import streamlit as st
import requests

st.title("DBT Impact Analysis")

BASE = "http://127.0.0.1:8000"

tab1, tab2 = st.tabs(["Impact Analysis", "Violations"])

# --- Impact ---
with tab1:
    models = requests.get(f"{BASE}/models").json()

    selected_model = st.selectbox("Select Model", models)

    columns = requests.get(f"{BASE}/columns/{selected_model}").json()

    selected_column = st.selectbox("Select Column", columns)

    # Button to fetch impact once
    if st.button("Check Impact"):
        # fetch and store result in session state
        response = requests.get(
            f"{BASE}/impact",
            params={"model": selected_model, "column": selected_column},
        )
        try:
            data = response.json()
        except Exception:
            data = {"error": "Unable to parse JSON", "text": response.text}
        st.session_state["impact_data"] = data
        # default view mode is Graph
        st.session_state["view_mode"] = "Graph"
    # After we have data, show toggle buttons side‑by‑side
    if "impact_data" in st.session_state:
        col_graph, col_list = st.columns([1, 1])
        with col_graph:
            if st.button("Graph"):
                st.session_state["view_mode"] = "Graph"
        with col_list:
            if st.button("List"):
                st.session_state["view_mode"] = "List"
        # Render according to selected view
        if st.session_state.get("view_mode") == "Graph":
            edges = st.session_state["impact_data"].get("edges", {})
            # Build GraphViz using actual edges to avoid misleading direct links
            dot = "digraph Impact {\n    rankdir=LR;\n    node [shape=box, style=filled, color=lightblue];\n"
            for upstream, downs in edges.items():
                for dep in downs:
                    dot += f'    "{upstream}" -> "{dep}";\n'
            dot += "}"
            st.graphviz_chart(dot)

        else:
            st.json(st.session_state["impact_data"])

# --- Violations ---
with tab2:
    if st.button("Check Hardcoded Tables"):
        res = requests.get(f"{BASE}/violations")
        # st.write(res.json())
        st.write("STATUS:", res.status_code)
        st.write("TEXT:", res.text)