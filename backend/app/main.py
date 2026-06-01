# app/main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl
from fastapi.middleware.cors import CORSMiddleware
import os
from typing import Literal, Dict, Any, Optional
from app.services.youtube_service import (
    extract_video_id,
    get_youtube_metadata,
    get_youtube_transcript_placeholder,
    YouTubeVideoDataError,
)
from app.rag.vector_store import upsert_video_chunks
from dotenv import load_dotenv
load_dotenv()


class VideoPlatform(str):
    YOUTUBE = "youtube"
    INSTAGRAM = "instagram"
    UNKNOWN = "unknown"


class VideoInfo(BaseModel):
    url: HttpUrl
    platform: Literal["youtube", "instagram", "unknown"]
    video_id: Optional[str] = None
    title: Optional[str] = None
    creator: Optional[str] = None
    views: Optional[int] = None
    likes: Optional[int] = None
    comments: Optional[int] = None
    engagement_rate: Optional[float] = None
    follower_count: Optional[int] = None
    hashtags: Optional[list[str]] = None
    upload_date: Optional[str] = None
    duration_seconds: Optional[int] = None
    duration: Optional[str] = None
    transcript: Optional[str] = None
    thumbnail_url: Optional[str] = None


class VideoPairRequest(BaseModel):
    video_a_url: HttpUrl
    video_b_url: HttpUrl


class VideoPairResponse(BaseModel):
    video_a: VideoInfo
    video_b: VideoInfo
    message: str


app = FastAPI(title="RAG Video Analyzer API")

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


def detect_platform(url: str) -> Literal["youtube", "instagram", "unknown"]:
    if "youtube.com" in url or "youtu.be" in url:
        return "youtube"
    if "instagram.com" in url:
        return "instagram"
    return "unknown"


def compute_engagement_rate(likes: Optional[int], comments: Optional[int], views: Optional[int]) -> Optional[float]:
    if likes is None or comments is None or views is None or views == 0:
        return None
    return (likes + comments) / views * 100.0


def process_single_video(url: str, label: str) -> VideoInfo:
    platform = detect_platform(url)
    video_data: Dict[str, Any] = {
        "url": url,
        "platform": platform,
    }

    if platform == "youtube":
        video_id = extract_video_id(url)
        if not video_id:
            # If ID extraction fails, still return a stub; don't crash the whole request
            video_data["video_id"] = None
            video_data["title"] = None
            video_data["creator"] = None
            video_data["views"] = None
            video_data["likes"] = None
            video_data["comments"] = None
            video_data["upload_date"] = None
            video_data["duration_seconds"] = None
            video_data["duration"] = None
            video_data["thumbnail_url"] = None
            video_data["transcript"] = ""
            return VideoInfo(**video_data)

        video_data["video_id"] = video_id

        try:
            metadata = get_youtube_metadata(url)
        except YouTubeVideoDataError as e:
            # Log internally if you want, but don't kill the request
            metadata = {
                "title": None,
                "channel": None,
                "views": None,
                "likes": None,
                "comments": None,
                "publish_date": None,
                "duration_seconds": None,
                "duration": None,
                "thumbnail_url": None,
                "description": "",
            }

        # Placeholder transcript for now; avoids youtube-transcript-api issues
        transcript = get_youtube_transcript_placeholder(label)

        video_data.update(
            {
                "title": metadata.get("title"),
                "creator": metadata.get("channel"),
                "views": metadata.get("views"),
                "likes": metadata.get("likes"),
                "comments": metadata.get("comments"),
                "upload_date": metadata.get("publish_date"),
                "duration_seconds": metadata.get("duration_seconds"),
                "duration": metadata.get("duration"),
                "thumbnail_url": metadata.get("thumbnail_url"),
                "transcript": transcript,
            }
        )

        engagement_rate = compute_engagement_rate(
            likes=video_data.get("likes"),
            comments=video_data.get("comments"),
            views=video_data.get("views"),
        )
        video_data["engagement_rate"] = engagement_rate


    elif platform == "instagram":
        # Placeholder: we’ll implement real IG logic next
        video_data["title"] = None
        video_data["creator"] = None
        video_data["views"] = None
        video_data["likes"] = None
        video_data["comments"] = None
        video_data["engagement_rate"] = None
        video_data["transcript"] = None
    else:
        # Unknown platform
        video_data["title"] = None
        video_data["creator"] = None

    return VideoInfo(**video_data)


@app.post("/api/process_videos", response_model=VideoPairResponse)
def process_videos(payload: VideoPairRequest):
    video_a_info = process_single_video(str(payload.video_a_url), "Video A")
    video_b_info = process_single_video(str(payload.video_b_url), "Video B")

    # Upsert chunks for RAG
    try:
        upsert_video_chunks(
            video_id=video_a_info.video_id or "unknown",
            video_label="A",
            transcript=video_a_info.transcript or "",
            metadata={
                "video_id": video_a_info.video_id,
                "platform": video_a_info.platform,
                "title": video_a_info.title,
                "creator": video_a_info.creator,
            },
        )

        upsert_video_chunks(
            video_id=video_b_info.video_id or "unknown",
            video_label="B",
            transcript=video_b_info.transcript or "",
            metadata={
                "video_id": video_b_info.video_id,
                "platform": video_b_info.platform,
                "title": video_b_info.title,
                "creator": video_b_info.creator,
            },
        )
    except Exception as e:
        # In demo, we don't fail the whole request if embeddings/storage fails.
        # You can log this in a real app.
        print(f"[WARN] Failed to upsert video chunks: {e}")

    return VideoPairResponse(
        video_a=video_a_info,
        video_b=video_b_info,
        message="Videos processed and chunks stored for RAG.",
    )

