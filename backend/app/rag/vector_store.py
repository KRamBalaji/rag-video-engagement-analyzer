# app/rag/vector_store.py

import os
from typing import List, Dict, Any

from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from sentence_transformers import SentenceTransformer
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.vectorstores import VectorStoreRetriever


# Singleton-style store in process
_chroma_instance: Chroma | None = None

def get_vector_store() -> Chroma:
    global _chroma_instance
    if _chroma_instance is not None:
        return _chroma_instance

    persist_dir = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")

    # Open‑source embeddings: BGE or E5
    model_name = os.getenv("EMBEDDING_MODEL_NAME", "BAAI/bge-small-en-v1.5")
    embeddings = HuggingFaceEmbeddings(
        model_name=model_name,
        model_kwargs={"device": "cpu"},
    )

    _chroma_instance = Chroma(
        collection_name="video_chunks",
        embedding_function=embeddings,
        persist_directory=persist_dir,
    )
    return _chroma_instance


def upsert_video_chunks(
    video_id: str,
    video_label: str,  # "A" or "B"
    transcript: str,
    metadata: Dict[str, Any],
) -> List[str]:
    """
    Chunk the transcript and upsert into Chroma.

    Each chunk is tagged with:
      - video_id (e.g., "A" or "B")
      - source_video_id (platform-specific id, e.g., YouTube ID)
      - title, creator, etc. from metadata
    """
    from app.rag.chunking import chunk_transcript

    if not transcript:
        return []

    store = get_vector_store()
    chunks = chunk_transcript(transcript)

    docs: List[Document] = []
    ids: List[str] = []

    for idx, chunk in enumerate(chunks):
        doc_metadata = {
            "video_label": video_label,
            "source_video_id": metadata.get("video_id"),
            "platform": metadata.get("platform"),
            "title": metadata.get("title"),
            "creator": metadata.get("creator"),
            "chunk_index": idx,
            "views": metadata.get("views"),
            "likes": metadata.get("likes"),
            "comments": metadata.get("comments"),
            "engagement_rate": metadata.get("engagement_rate"),
        }
        docs.append(Document(page_content=chunk, metadata=doc_metadata))
        ids.append(f"{video_label}_{metadata.get('video_id')}_{idx}")

    if not docs:
        return []

    store.add_documents(documents=docs, ids=ids)
    store.persist()

    return ids

def get_retriever(k: int = 6):
    store = get_vector_store()
    return store.as_retriever(search_kwargs={"k": k})

def clear_vector_store():
    store = get_vector_store()
    store.delete(ids=None, where={})
    store.persist()