# app/main.py
from fastapi import FastAPI

app = FastAPI(title="RAG Video Analyzer API")


@app.get("/health")
def health_check():
    return {"status": "ok"}
