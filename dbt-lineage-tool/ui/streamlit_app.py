import streamlit as st
import requests

st.set_page_config(layout="wide")
st.title("DBT Impact Analysis")

BASE = "http://127.0.0.1:8000"

tab1, tab2 = st.tabs(["Impact Analysis", "Violations"])

# Initialize session state for persistence
if "impact_data" not in st.session_state:
    st.session_state["impact_data"] = None
if "view_mode" not in st.session_state:
    st.session_state["view_mode"] = "Graph"

# -------------------------
# IMPACT TAB
# -------------------------
with tab1:
    try:
        # Load models and columns
        models = requests.get(f"{BASE}/models").json()
        selected_model = st.selectbox("Select Model", models)

        columns = requests.get(f"{BASE}/columns/{selected_model}").json()
        selected_column = st.selectbox("Select Column", columns)
    except Exception as e:
        st.error(f"Backend Connection Error: {e}")
        st.stop()

    if st.button("Check Impact", type="primary"):
        response = requests.get(
            f"{BASE}/impact",
            params={"model": selected_model, "column": selected_column},
        )
        if response.status_code == 200:
            st.session_state["impact_data"] = response.json()
            # Force view to graph on new search
            st.session_state["view_mode"] = "Graph"
        else:
            st.error("Error fetching impact data.")

    # Only show results if we have data
    if st.session_state["impact_data"]:
        st.divider()
        
        # Toggle Buttons
        c1, c2 = st.columns([1, 10])
        with c1:
            if st.button("Graph View"):
                st.session_state["view_mode"] = "Graph"
        with c2:
            if st.button("List View"):
                st.session_state["view_mode"] = "List"

        if st.session_state["view_mode"] == "Graph":
            edges = st.session_state["impact_data"].get("edges", {})
            
            if not edges:
                st.info("No downstream dependencies found for this column selection.")
            else:
                # DOT language for Graphviz
                # ranksep adds horizontal space; nodesep adds vertical space
                dot_code = f"""
                digraph G {{
                    rankdir="LR";
                    graph [ranksep="1.8", nodesep="0.5", pad="0.5"];
                    node [shape=box, style="filled,rounded", color="#AED6F1", 
                          fontname="Helvetica", fontsize=11, margin="0.2,0.1"];
                    edge [color="#5D6D7E", arrowhead=vee, arrowsize=0.8];

                    # The source model
                    "{selected_model}" [fillcolor="#3498DB", fontcolor=white, style="filled,bold"];
                """

                # Build the relationships
                for upstream, downs in edges.items():
                    for dep in downs:
                        dot_code += f'    "{upstream}" -> "{dep}";\n'
                
                dot_code += "}"
                
                # Render with container_width=True to fix the "squished" issue
                st.graphviz_chart(dot_code, use_container_width=True)

        else:
            # List Section
            st.subheader("Downstream Impact List")
            impacted_list = st.session_state["impact_data"].get("impacted_nodes", [])
            if impacted_list:
                for item in impacted_list:
                    st.text(f"• {item}")
            
            with st.expander("View Raw JSON"):
                st.json(st.session_state["impact_data"])

# -------------------------
# VIOLATIONS TAB
# -------------------------
with tab2:
    st.subheader("🚩 Policy Audit: Hardcoded References")
    
    if st.button("Run Violation Scan"):
        res = requests.get(f"{BASE}/violations")
        if res.status_code == 200:
            violations = res.json()
            if not violations:
                st.success("✅ No violations found!")
            else:
                total_v = sum(len(tables) for tables in violations.values())
                m1, m2 = st.columns(2)
                m1.metric("Impacted Models", len(violations))
                m2.metric("Hardcoded Tables", total_v)
                
                for model, tables in violations.items():
                    with st.expander(f"📍 {model}"):
                        st.table({"Hardcoded Table References": tables})
        else:
            st.error("Could not fetch violations.")