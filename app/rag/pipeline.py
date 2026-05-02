import gc
import os
from collections.abc import Iterator
from pathlib import Path

from app.ingest.chunker import chunk_pages
from app.ingest.pdf_parser import extract_pdf_pages
from app.rag.embeddings import embed_texts
from app.rag.ollama_client import generate_answer
from app.rag.vector_store import (
    add_chunks,
    get_collection,
    query_chunks,
    reset_collection,
)


PDF_DIR = Path("data") / "pdfs"
INGEST_BATCH_SIZE = 64


def _get_ingest_batch_size() -> int:
    value = os.getenv("RAG_INGEST_BATCH_SIZE")
    if not value:
        return INGEST_BATCH_SIZE

    try:
        return max(1, int(value))
    except ValueError:
        return INGEST_BATCH_SIZE


def _batched(items: list[dict], batch_size: int) -> Iterator[list[dict]]:
    for index in range(0, len(items), batch_size):
        yield items[index : index + batch_size]


def ingest_pdfs(pdf_dir: str | Path = PDF_DIR) -> dict:
    directory = Path(pdf_dir)
    directory.mkdir(parents=True, exist_ok=True)
    pdf_paths = sorted(directory.glob("*.pdf"))

    reset_collection()

    page_count = 0
    chunk_count = 0
    ingest_batch_size = _get_ingest_batch_size()
    for pdf_path in pdf_paths:
        pages = extract_pdf_pages(pdf_path)
        page_count += len(pages)

        chunks = chunk_pages(pages)
        for chunk_batch in _batched(chunks, ingest_batch_size):
            embeddings = embed_texts([chunk["text"] for chunk in chunk_batch])
            chunk_count += add_chunks(chunk_batch, embeddings, reset=False)
            del embeddings

        del pages, chunks
        gc.collect()

    return {
        "pdfs": len(pdf_paths),
        "pages": page_count,
        "chunks": chunk_count,
    }


def format_context(chunks: list[dict]) -> str:
    parts: list[str] = []
    for index, chunk in enumerate(chunks, start=1):
        metadata = chunk["metadata"]
        label = f"[{index}] {metadata['source']} page {metadata['page']}"
        parts.append(f"{label}\n{chunk['text']}")
    return "\n\n".join(parts)


def answer_question(question: str, top_k: int = 3) -> dict:
    query_embedding = embed_texts([question])[0]
    chunks = query_chunks(query_embedding, top_k=top_k)
    if not chunks:
        return {
            "answer": "No indexed PDF chunks were found. Add PDFs to data/pdfs and run ingestion.",
            "sources": [],
        }

    context = format_context(chunks)
    answer = generate_answer(question, context)

    return {
        "answer": answer,
        "sources": [chunk["metadata"] for chunk in chunks],
    }


def index_status() -> dict:
    collection = get_collection()
    return {"chunks": collection.count()}
