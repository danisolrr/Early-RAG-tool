import re


def _clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def chunk_pages(
    pages: list[dict],
    chunk_size: int = 800,
    overlap: int = 150,
) -> list[dict]:
    """Split page text into overlapping character chunks."""
    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")

    chunks: list[dict] = []
    for page in pages:
        text = _clean_text(page["text"])
        if not text:
            continue

        start = 0
        chunk_number = 1
        while start < len(text):
            end = min(start + chunk_size, len(text))
            chunk_text = text[start:end].strip()
            if chunk_text:
                chunks.append(
                    {
                        "id": f"{page['source']}::p{page['page']}::c{chunk_number}",
                        "text": chunk_text,
                        "metadata": {
                            "source": page["source"],
                            "path": page["path"],
                            "page": page["page"],
                            "chunk": chunk_number,
                        },
                    }
                )

            if end == len(text):
                break
            start = max(0, end - overlap)
            chunk_number += 1

    return chunks
