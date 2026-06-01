# backend/app/services/youtube_service.py

from typing import Optional, Dict, Any
from urllib.parse import urlparse, parse_qs
from datetime import timedelta

from yt_dlp import YoutubeDL


class YouTubeVideoDataError(Exception):
    """Custom exception for YouTube data fetching errors."""
    pass


def extract_video_id(url: str) -> Optional[str]:
    """
    Extracts the YouTube video ID from various URL formats.

    Supports:
    - https://www.youtube.com/watch?v=VIDEO_ID
    - https://youtube.com/watch?v=VIDEO_ID
    - https://youtu.be/VIDEO_ID
    - https://www.youtube.com/embed/VIDEO_ID
    """
    parsed = urlparse(url)

    # Standard watch URL
    if parsed.hostname in ("www.youtube.com", "youtube.com"):
        if parsed.path == "/watch":
            return parse_qs(parsed.query).get("v", [None])[0]
        # Embedded
        if parsed.path.startswith("/embed/"):
            parts = parsed.path.split("/")
            if len(parts) >= 3:
                return parts[2]
        # Old-style /v/VIDEO_ID
        if parsed.path.startswith("/v/"):
            parts = parsed.path.split("/")
            if len(parts) >= 3:
                return parts[2]

    # Short URL
    if parsed.hostname == "youtu.be":
        return parsed.path.lstrip("/")

    return None


def get_youtube_metadata(url: str) -> Dict[str, Any]:
    """
    Fetch metadata using yt-dlp.

    We only need metadata (no download), so we call extract_info(download=False).
    """
    ydl_opts = {
        "quiet": True,
        "skip_download": True,
        # We are not doing any muxing/transcoding here, just metadata.
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
    except Exception as e:
        raise YouTubeVideoDataError(f"Failed to fetch metadata via yt-dlp: {e}") from e

    # yt-dlp returns a rich info dict; we extract what we care about.
    title = info.get("title")
    channel = info.get("uploader") or info.get("channel")
    views = info.get("view_count") or 0
    likes = info.get("like_count")
    comments = info.get("comment_count")
    upload_date_raw = info.get("upload_date")  # e.g. "20250131"
    description = info.get("description") or ""
    thumbnail_url = info.get("thumbnail")
    duration_seconds = info.get("duration") or 0

    # Convert upload_date_raw to ISO date string if present.
    upload_date_iso = None
    if upload_date_raw and len(upload_date_raw) == 8:
        year = int(upload_date_raw[0:4])
        month = int(upload_date_raw[4:6])
        day = int(upload_date_raw[6:8])
        upload_date_iso = f"{year:04d}-{month:02d}-{day:02d}"

    duration = str(timedelta(seconds=duration_seconds))

    return {
        "title": title,
        "channel": channel,
        "views": views,
        "likes": likes,
        "comments": comments,
        "description": description,
        "thumbnail_url": thumbnail_url,
        "publish_date": upload_date_iso,
        "duration_seconds": duration_seconds,
        "duration": duration,
    }


def get_youtube_transcript_placeholder(video_label: str) -> str:
    """
    Placeholder for transcript retrieval.

    For now, we don't use youtube-transcript-api to avoid library issues.
    In a production version, you would:
      - Use yt-dlp to download audio, then
      - Run Whisper or a hosted transcription API to get the transcript.

    We return a simple placeholder string so the rest of the RAG pipeline
    (chunking, embeddings, etc.) can be implemented and demonstrated.
    """
    return (
        f"This is a placeholder transcript for {video_label}. "
        f"In a production system, this would be generated using yt-dlp to "
        f"download audio and Whisper (or a hosted transcription API) to "
        f"produce accurate subtitles."
    )
