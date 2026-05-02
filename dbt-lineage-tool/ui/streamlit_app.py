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

    if st.button("Check Impact"):
        res = requests.get(
            f"{BASE}/impact",
            params={"model": selected_model, "column": selected_column}
        )
        # st.write(res.json())
        st.write("STATUS:", res.status_code)
        st.write("TEXT:", res.text)

# --- Violations ---
with tab2:
    if st.button("Check Hardcoded Tables"):
        res = requests.get(f"{BASE}/violations")
        # st.write(res.json())
        st.write("STATUS:", res.status_code)
        st.write("TEXT:", res.text)