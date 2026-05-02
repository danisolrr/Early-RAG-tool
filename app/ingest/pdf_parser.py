from pathlib import Path

import fitz


def extract_pdf_pages(pdf_path: str | Path) -> list[dict]:
    """Extract text from a PDF one page at a time."""
    path = Path(pdf_path)
    pages: list[dict] = []

    with fitz.open(path) as document:
        for page_index, page in enumerate(document, start=1):
            text = page.get_text("text").strip()
            if text:
                pages.append(
                    {
                        "source": path.name,
                        "path": str(path),
                        "page": page_index,
                        "text": text,
                    }
                )

    return pages


def load_pdfs(pdf_dir: str | Path) -> list[dict]:
    """Read every PDF in a directory and return extracted page records."""
    directory = Path(pdf_dir)
    if not directory.exists():
        directory.mkdir(parents=True, exist_ok=True)
        return []

    pages: list[dict] = []
    for pdf_path in sorted(directory.glob("*.pdf")):
        pages.extend(extract_pdf_pages(pdf_path))

    return pages
