import os
from functools import lru_cache

from sentence_transformers import SentenceTransformer


MODEL_NAME = "all-MiniLM-L6-v2"
DEFAULT_BATCH_SIZE = 16


def _get_embedding_device() -> str:
    configured_device = os.getenv("RAG_EMBEDDING_DEVICE", "auto").lower()
    if configured_device != "auto":
        return configured_device

    try:
        import torch
    except ImportError:
        return "cpu"

    return "cuda" if torch.cuda.is_available() else "cpu"


def _get_embedding_batch_size() -> int:
    value = os.getenv("RAG_EMBEDDING_BATCH_SIZE")
    if not value:
        return DEFAULT_BATCH_SIZE

    try:
        return max(1, int(value))
    except ValueError:
        return DEFAULT_BATCH_SIZE


@lru_cache(maxsize=1)
def get_embedding_model() -> SentenceTransformer:
    return SentenceTransformer(MODEL_NAME, device=_get_embedding_device())


def embed_texts(texts: list[str], batch_size: int | None = None) -> list[list[float]]:
    if not texts:
        return []

    model = get_embedding_model()
    embeddings = model.encode(
        texts,
        batch_size=batch_size or _get_embedding_batch_size(),
        normalize_embeddings=True,
        show_progress_bar=False,
    )
    return embeddings.tolist()
