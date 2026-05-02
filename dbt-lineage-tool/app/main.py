from fastapi import FastAPI
from app.parser import ManifestLoader
from app.lineage import LineageEngine
from app.violations import ViolationDetector

loader = ManifestLoader("data/manifest.json")

engine = LineageEngine(loader)
engine.build()

detector = ViolationDetector(loader)

app = FastAPI()

@app.get("/")
def root():
    return {"status": "running"}

@app.get("/models")
def models():
    return list(loader.get_models().keys())

@app.get("/columns/{model}")
def columns(model: str):
    return loader.get_columns(model)

@app.get("/impact")
def impact(model: str, column: str):
    return {
        "downstream": engine.downstream(model, column)
    }

@app.get("/violations")
def violations():
    return detector.find_hardcoded_tables()