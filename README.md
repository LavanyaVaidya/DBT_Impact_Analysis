# DBT Lineage & Impact Analysis Tool

A lightweight internal tool to analyze lineage, column usage, and SQL violations in a dbt project using the `manifest.json`.

It helps you understand how changes in a dbt model impact downstream models and detects unsafe SQL patterns like hardcoded table references that bypass `ref()` and `source()`.

Built with FastAPI backend and Streamlit UI.

---

# Project Structure

dbt-lineage-tool/
│
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── parser.py
│   ├── lineage.py
│   ├── violations.py
│
├── ui/
│   └── streamlit_app.py
│
├── data/
│   └── manifest.json   (copy from dbt_project/target/manifest.json)
│
├── requirements.txt
├── .env
└── README.md

---

# Setup Instructions

## 1. Clone repository

---

## 2. Create virtual environment (Windows)
python -m venv venv
venv\Scripts\activate

---

## 3. Install dependencies
pip install -r requirements.txt

---

## 4. Generate and add dbt manifest

From your dbt project:
dbt docs generate

Copy:
dbt_project/target/manifest.json

Paste into:
dbt-lineage-tool/data/manifest.json

---

## 5. Run backend (FastAPI)
uvicorn app.main:app --reload

Backend runs at:
http://127.0.0.1:8000

---

## 6. Run frontend (Streamlit)
streamlit run ui/streamlit_app.py

UI runs at:
http://localhost:8501

---

# Features

## Lineage Tracking
Builds downstream dependency graph of dbt models using manifest data.

## Column Extraction
Extracts column-level metadata from dbt manifest and SQL parsing fallback.

## Violation Detection
Detects:
- Hardcoded table usage
- Missing ref()/source() usage
- Non-dbt managed dependencies

---

# API Endpoints

- /models → list dbt models
- /lineage?model=xyz → downstream impact
- /violations?model=xyz → SQL violations

---

# Requirements

- Python 3.10+
- dbt project with manifest.json
- No database required (works purely on dbt artifacts)

---

# Notes

- Always run FastAPI before Streamlit
- If models/columns are empty, regenerate manifest:
  dbt docs generate
- This tool is designed for internal lineage + governance visibility