# app/main.py
import asyncio
from fastapi.concurrency import run_in_threadpool
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, HttpUrl
from fastapi.middleware.cors import CORSMiddleware
import os
import requests
from fastapi.responses import StreamingResponse
from urllib.parse import unquote
from typing import List, Literal, Dict, Any, Optional, Union
from app.services.youtube_service import (
    extract_video_id,
    get_youtube_metadata,
    get_youtube_transcript_placeholder,
    YouTubeVideoDataError,
)
from app.services.instagram_service import (
    get_instagram_metadata,
    InstagramVideoDataError,
)
from app.rag.vector_store import upsert_video_chunks, get_retriever, clear_vector_store
from app.services.transcript_service import get_transcript_fast, TranscriptError
from dotenv import load_dotenv
load_dotenv()
from sentence_transformers import SentenceTransformer
from groq import Groq

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str

class ChatRequest(BaseModel):
    session_id: str
    message: str
    history: List[ChatMessage] = []

class ChatResponse(BaseModel):
    answer: str
    citations: List[dict]


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


def parse_int(value: Any) -> Optional[int]:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        try:
            return int(float(value))
        except (TypeError, ValueError):
            return None


async def process_single_video(url: str, label: str) -> VideoInfo:
    platform = detect_platform(url)
    video_data: Dict[str, Any] = {
        "url": url,
        "platform": platform,
    }

    if platform == "youtube":
        video_id = extract_video_id(url)
        if not video_id:
            # If ID extraction fails, still return a stub; don't crash the whole request
            video_data.update(
                {
                    "video_id": None,
                    "title": None,
                    "creator": None,
                    "views": None,
                    "likes": None,
                    "comments": None,
                    "upload_date": None,
                    "duration_seconds": None,
                    "duration": None,
                    "thumbnail_url": None,
                    "transcript": "",
                }
            )
            return VideoInfo(**video_data)

        video_data["video_id"] = video_id

        metadata_task = run_in_threadpool(get_youtube_metadata, url)
        transcript_task = run_in_threadpool(get_transcript_fast, url, label)

        metadata = None
        transcript = ""

        metadata_result, transcript_result = await asyncio.gather(
            metadata_task,
            transcript_task,
            return_exceptions=True,
        )

        if isinstance(metadata_result, YouTubeVideoDataError) or isinstance(metadata_result, Exception):
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
        else:
            metadata = metadata_result

        if isinstance(transcript_result, TranscriptError) or isinstance(transcript_result, Exception):
            print(f"[WARN] Transcript fetch failed for {label}: {transcript_result}")
            transcript = get_youtube_transcript_placeholder(label)
        else:
            transcript = transcript_result or get_youtube_transcript_placeholder(label)

        video_data.update(
            {
                "title": metadata.get("title"),
                "creator": metadata.get("channel"),
                "views": parse_int(metadata.get("views")),
                "likes": parse_int(metadata.get("likes")),
                "comments": parse_int(metadata.get("comments")),
                "upload_date": metadata.get("publish_date"),
                "duration_seconds": parse_int(metadata.get("duration_seconds")),
                "duration": metadata.get("duration"),
                "thumbnail_url": metadata.get("thumbnail_url"),
                "transcript": transcript,
            }
        )

        video_data["engagement_rate"] = compute_engagement_rate(
            likes=video_data.get("likes"),
            comments=video_data.get("comments"),
            views=video_data.get("views"),
        )


    elif platform == "instagram":
        try:
            ig_meta = get_instagram_metadata(url)
        except InstagramVideoDataError as e:
            print(f"[WARN] Failed to fetch Instagram metadata for {label}: {e}")
            ig_meta = {
                "title": None,
                "creator": None,
                "views": None,
                "likes": None,
                "comments": None,
                "description": "",
                "hashtags": [],
                "upload_date": None,
                "thumbnail_url": None,
                "duration_seconds": None,
                "duration": None,
                "follower_count": None,
            }

        try:
            transcript = get_transcript_fast(url, label)
            if not transcript:
                transcript = (
                    f"This is a short placeholder transcript for {label} on Instagram. "
                    f"In production, we would transcribe the full Reel."
                )
        except TranscriptError as e:
            print(f"[WARN] Whisper transcript failed for Instagram {label}: {e}")
            transcript = (
                f"This is a placeholder transcript for {label} on Instagram. "
                f"Transcript generation failed or is disabled."
            )

        video_data.update(
            {
                "title": ig_meta.get("title"),
                "creator": ig_meta.get("creator"),
                "views": parse_int(ig_meta.get("views")),
                "likes": parse_int(ig_meta.get("likes")),
                "comments": parse_int(ig_meta.get("comments")),
                "upload_date": ig_meta.get("upload_date"),
                "duration_seconds": parse_int(ig_meta.get("duration_seconds")),
                "duration": ig_meta.get("duration"),
                "thumbnail_url": ig_meta.get("thumbnail_url"),
                "hashtags": ig_meta.get("hashtags"),
                "follower_count": parse_int(ig_meta.get("follower_count")),
                "transcript": transcript,
            }
        )

        engagement_rate = compute_engagement_rate(
            likes=video_data.get("likes"),
            comments=video_data.get("comments"),
            views=video_data.get("views"),
        )
        video_data["engagement_rate"] = engagement_rate

    return VideoInfo(**video_data)


@app.post("/api/process_videos", response_model=VideoPairResponse)
async def process_videos(payload: VideoPairRequest):
    try:
        clear_vector_store()
    except Exception as e:
        print(f"[WARN] Failed to clear vector store: {e}")

    video_a_info, video_b_info = await asyncio.gather(
        process_single_video(str(payload.video_a_url), "Video A"),
        process_single_video(str(payload.video_b_url), "Video B"),
    )

    try:
        await asyncio.gather(
            run_in_threadpool(
                upsert_video_chunks,
                video_a_info.video_id or "unknown",
                "A",
                video_a_info.transcript or "",
                {
                    "video_id": video_a_info.video_id,
                    "platform": video_a_info.platform,
                    "title": video_a_info.title,
                    "creator": video_a_info.creator,
                    "views": video_a_info.views,
                    "likes": video_a_info.likes,
                    "comments": video_a_info.comments,
                    "engagement_rate": video_a_info.engagement_rate,
                },
            ),
            run_in_threadpool(
                upsert_video_chunks,
                video_b_info.video_id or "unknown",
                "B",
                video_b_info.transcript or "",
                {
                    "video_id": video_b_info.video_id,
                    "platform": video_b_info.platform,
                    "title": video_b_info.title,
                    "creator": video_b_info.creator,
                    "views": video_b_info.views,
                    "likes": video_b_info.likes,
                    "comments": video_b_info.comments,
                    "engagement_rate": video_b_info.engagement_rate,
                },
            ),
        )
    except Exception as e:
        print(f"[WARN] Failed to upsert video chunks: {e}")

    return VideoPairResponse(
        video_a=video_a_info,
        video_b=video_b_info,
        message="Videos processed and chunks stored for RAG.",
    )

@app.post("/api/chat", response_model=ChatResponse)
def chat_rag(payload: ChatRequest):
    """
    RAG chat endpoint:
    - Uses Chroma retriever over video chunks.
    - Builds a prompt including engagement and metadata from last /api/process_videos call.
    - Returns answer + citations.
    """
    if groq_client is None:
        raise HTTPException(status_code=500, detail="LLM not configured (missing GROQ_API_KEY).")

    retriever = get_retriever(k=6)
    # Retrieve relevant chunks
    docs = retriever.invoke(payload.message)


    # Build context string + citations
    context_parts = []
    citations = []

    summary_by_label = {
        "A": {"views": None, "likes": None, "comments": None, "engagement_rate": None},
        "B": {"views": None, "likes": None, "comments": None, "engagement_rate": None},
    }


    for idx, doc in enumerate(docs):
        meta = doc.metadata or {}
        label = meta.get("video_label", "?")
        title = meta.get("title") or "Unknown title"
        creator = meta.get("creator") or "Unknown creator"
        chunk_index = meta.get("chunk_index", idx)
        views = meta.get("views")
        likes = meta.get("likes")
        comments = meta.get("comments")
        er = meta.get("engagement_rate")

        if label in summary_by_label:
            s = summary_by_label[label]
            if views is not None and s["views"] is None:
                s["views"] = views
            if likes is not None and s["likes"] is None:
                s["likes"] = likes
            if comments is not None and s["comments"] is None:
                s["comments"] = comments
            if er is not None and s["engagement_rate"] is None:
                s["engagement_rate"] = er

        stats_line = ""
        if views is not None:
            stats_line += f"Views: {views}. "
        if likes is not None:
            stats_line += f"Likes: {likes}. "
        if comments is not None:
            stats_line += f"Comments: {comments}. "
        if er is not None:
            stats_line += f"Engagement rate: {er:.2f}%. "

        context_parts.append(
            f"[Chunk {idx}] Video {label} | Title: {title} | Creator: {creator}\n"
            f"{stats_line}\n"
            f"{doc.page_content}"
        )

    citations.append(
        {
            "video_label": label,
            "chunk_index": chunk_index,
            "title": title,
            "creator": creator,
            "views": views,
            "likes": likes,
            "comments": comments,
            "engagement_rate": er,
        }
    )


    context_text = "\n\n".join(context_parts) if context_parts else "No relevant transcript chunks found."

    # Turn history into messages
    messages = [
        {
            "role": "system",
            "content": (
                "You are an assistant analyzing two social media videos, A and B. "
                "You are given transcript chunks with metadata. Answer questions about:\n"
                "- Why A may have higher engagement than B\n"
                "- Engagement rates\n"
                "- Hooks in the first 5 seconds\n"
                "- Creator and follower information\n"
                "- Suggestions to improve B based on what worked in A\n\n"
                "Use ONLY the provided context and known numeric metadata. "
                "Always mention which video (A or B) and which chunk indices you are using as evidence. "
                "If you don't know something, say so honestly."
            ),
        }
    ]

    # Append conversation history
    for msg in payload.history:
        messages.append({"role": msg.role, "content": msg.content})

    # Add current user message with context
    messages.append(
        {
            "role": "user",
            "content": f"Context:\n{context_text}\n\nUser question: {payload.message}",
        }
    )

    try:
        completion = groq_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            temperature=0.4,
        )
        answer = completion.choices[0].message.content
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Groq LLM error: {e}")


    return ChatResponse(answer=answer, citations=citations)

@app.get("/proxy-thumbnail")
def proxy_thumbnail(url: str = Query(..., description="Upstream image URL")):
    """
    Simple image proxy to bypass hotlink blocking from Instagram's CDN.
    The frontend calls this instead of the IG URL directly.
    """
    try:
        # Decode URL if it was encoded on the frontend
        target_url = unquote(url)

        # Stream the image from Instagram
        resp = requests.get(target_url, stream=True, timeout=10)
        resp.raise_for_status()

        content_type = resp.headers.get("Content-Type", "image/jpeg")

        return StreamingResponse(
            resp.raw,
            media_type=content_type,
        )
    except Exception as e:
        # You can log e here if needed
        raise HTTPException(status_code=502, detail=f"Failed to fetch thumbnail: {e}")