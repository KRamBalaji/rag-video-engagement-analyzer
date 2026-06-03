# backend/app/services/instagram_service.py

from typing import Dict, Any, Optional, List
from datetime import timedelta
import re

from yt_dlp import YoutubeDL


class InstagramVideoDataError(Exception):
    """Custom exception for Instagram data fetching errors."""
    pass


def extract_hashtags(text: Optional[str]) -> List[str]:
    if not text:
        return []
    return re.findall(r"#\w+", text)


def get_instagram_metadata(url: str) -> Dict[str, Any]:
    """
    Fetch metadata for an Instagram Reel using yt-dlp.
    We rely on yt-dlp's JSON info since IG doesn't have a public metadata API.
    """
    ydl_opts = {
        "quiet": True,
        "skip_download": True,
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
    except Exception as e:
        raise InstagramVideoDataError(f"Failed to fetch IG metadata via yt-dlp: {e}") from e

    title = info.get("title")
    creator = info.get("uploader") or info.get("uploader_id")
    view_count = info.get("view_count") or 0
    like_count = info.get("like_count")
    comment_count = info.get("comment_count")
    description = info.get("description") or ""
    upload_date_raw = info.get("upload_date")  # "YYYYMMDD" if present
    thumbnail_url = info.get("thumbnail")
    duration_seconds = info.get("duration") or 0

    upload_date_iso = None
    if upload_date_raw and len(upload_date_raw) == 8:
        year = int(upload_date_raw[0:4])
        month = int(upload_date_raw[4:6])
        day = int(upload_date_raw[6:8])
        upload_date_iso = f"{year:04d}-{month:02d}-{day:02d}"

    duration = str(timedelta(seconds=duration_seconds))
    hashtags = extract_hashtags(description)

    # Follower count is tricky; yt-dlp may not expose it reliably.
    # We leave it as None for now and explain this trade-off in README.
    follower_count = None

    return {
        "title": title,
        "creator": creator,
        "views": view_count,
        "likes": like_count,
        "comments": comment_count,
        "description": description,
        "hashtags": hashtags,
        "upload_date": upload_date_iso,
        "thumbnail_url": thumbnail_url,
        "duration_seconds": duration_seconds,
        "duration": duration,
        "follower_count": follower_count,
    }
