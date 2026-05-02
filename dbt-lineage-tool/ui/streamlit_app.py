import streamlit as st
import streamlit.components.v1 as components
import networkx as nx
import matplotlib.pyplot as plt
import io

st.title("DBT Impact Analysis")

BASE = "http://127.0.0.1:8000"

tab1, tab2 = st.tabs(["Impact Analysis", "Violations"])

# -------------------------
# IMPACT TAB
# -------------------------
with tab1:

    import requests

    models = requests.get(f"{BASE}/models").json()
    selected_model = st.selectbox("Select Model", models)

    columns = requests.get(f"{BASE}/columns/{selected_model}").json()
    selected_column = st.selectbox("Select Column", columns)

    if st.button("Check Impact"):
        response = requests.get(
            f"{BASE}/impact",
            params={"model": selected_model, "column": selected_column},
        )

        try:
            data = response.json()
        except Exception:
            data = {"error": response.text}

        st.session_state["impact_data"] = data
        st.session_state["view_mode"] = "Graph"

    if st.session_state.get("impact_data"):

        col_graph, col_list = st.columns(2)

        with col_graph:
            if st.button("Graph"):
                st.session_state["view_mode"] = "Graph"

        with col_list:
            if st.button("List"):
                st.session_state["view_mode"] = "List"

        if st.session_state.get("view_mode") == "Graph":

            edges = st.session_state["impact_data"].get("edges", {})

            G = nx.DiGraph()

            for upstream, downs in edges.items():
                for dep in downs:
                    G.add_edge(upstream, dep)

            # -------------------------
            # CLEAN LEFT → RIGHT LAYOUT
            # -------------------------
            try:
                from networkx.drawing.nx_agraph import graphviz_layout
                pos = graphviz_layout(G, prog="dot")
            except:
                pos = nx.spring_layout(G, seed=42)

            fig, ax = plt.subplots(figsize=(12, 6))
            nx.draw(
                G,
                pos,
                with_labels=True,
                node_color="lightblue",
                node_size=2000,
                arrows=True,
                font_size=8,
                ax=ax
            )

            st.pyplot(fig)

        else:
            st.json(st.session_state["impact_data"])

# -------------------------
# VIOLATIONS TAB
# -------------------------
with tab2:

    if st.button("Check Hardcoded Tables"):
        res = requests.get(f"{BASE}/violations")
        st.write("STATUS:", res.status_code)
        st.write("TEXT:", res.text)