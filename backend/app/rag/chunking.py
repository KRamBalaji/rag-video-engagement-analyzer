# app/rag/chunking.py

from typing import List
from langchain_text_splitters import RecursiveCharacterTextSplitter


def chunk_transcript(text: str) -> List[str]:
    """
    Split transcript text into overlapping chunks for RAG.

    You can later tune chunk_size/chunk_overlap and defend those choices.
    """
    if not text:
        return []

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,      # ~750 tokens-ish
        chunk_overlap=200,    # keep continuity between chunks
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = splitter.split_text(text)
    return chunks
