# app/main.py
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import os

class VideoPairRequest(BaseModel):
    video_a_url: str
    video_b_url: str

class VideoPairResponse(BaseModel):
    video_a_url: str
    video_b_url: str
    message: str

app = FastAPI(title="RAG Video Analyzer API")

# Allow frontend (Next.js) to call this backend
frontend_origin = os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/api/process_videos", response_model=VideoPairResponse)
def process_videos(payload: VideoPairRequest):
    return {
        "video_a_url": payload.video_a_url,
        "video_b_url": payload.video_b_url,
        "message": "URLs received successfully. RAG processing will be added next.",
    }