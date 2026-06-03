# app/services/transcript_service.py

import os
import shutil
import tempfile
from typing import Optional
from dataclasses import dataclass

from yt_dlp import YoutubeDL
import whisper


class TranscriptError(Exception):
    pass


_WHISPER_MODEL_CACHE = {}


def load_whisper_model(model_name: str = "tiny.en"):
    if model_name not in _WHISPER_MODEL_CACHE:
        _WHISPER_MODEL_CACHE[model_name] = whisper.load_model(model_name)
    return _WHISPER_MODEL_CACHE[model_name]


def parse_vtt_subtitles(vtt_path: str) -> str:
    lines = []
    with open(vtt_path, "r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith("WEBVTT") or stripped.startswith("NOTE"):
                continue
            if "-->" in stripped:
                continue
            if stripped.isdigit():
                continue
            lines.append(stripped)
    return " ".join(lines).strip()


def get_subtitles_via_yt_dlp(url: str, lang: str = "en") -> Optional[str]:
    tmp_dir = tempfile.mkdtemp(prefix="rag_subtitles_")
    output_template = os.path.join(tmp_dir, "subtitle.%(ext)s")
    ydl_opts = {
        "quiet": True,
        "skip_download": True,
        "writesubtitles": True,
        "writeautomaticsub": True,
        "subtitleslangs": [lang],
        "subtitlesformat": "vtt",
        "outtmpl": output_template,
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        for root, _, files in os.walk(tmp_dir):
            for filename in files:
                if filename.endswith(".vtt"):
                    return parse_vtt_subtitles(os.path.join(root, filename))
    except Exception:
        return None
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    return None


def get_transcript_fast(url: str, video_label: str, model_name: str = "tiny.en") -> str:
    transcript = get_subtitles_via_yt_dlp(url)
    if transcript:
        return transcript
    return get_transcript_via_whisper(url, model_name=model_name)


def download_audio_to_tempfile(url: str) -> str:
    """
    Download audio from a video URL to a temporary file using yt-dlp.
    Returns the path to the audio file.
    """
    tmp_dir = tempfile.mkdtemp(prefix="rag_audio_")
    output_template = os.path.join(tmp_dir, "audio.%(ext)s")

    ydl_opts = {
        "quiet": True,
        "format": "bestaudio/best",
        "outtmpl": output_template,
    }

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        downloaded_path = ydl.prepare_filename(info)

    if not os.path.exists(downloaded_path):
        raise TranscriptError("Audio download failed, file not found.")

    return downloaded_path


def transcribe_audio(audio_path: str, model_name: str = "tiny.en") -> str:
    """
    Transcribe audio using open-source Whisper.
    """
    try:
        model = load_whisper_model(model_name)
        result = model.transcribe(audio_path, fp16=False, language="en")
        text = result.get("text", "").strip()
        return text
    except Exception as e:
        raise TranscriptError(f"Whisper transcription failed: {e}") from e


def get_transcript_via_whisper(url: str, model_name: str = "tiny.en") -> str:
    """
    High-level helper: download audio and transcribe it.
    """
    try:
        audio_path = download_audio_to_tempfile(url)
        text = transcribe_audio(audio_path, model_name=model_name)
        return text
    except TranscriptError:
        raise
    except Exception as e:
        raise TranscriptError(f"Transcript pipeline failed: {e}") from e
