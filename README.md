# Local PDF RAG

A small local Retrieval-Augmented Generation (RAG) app for asking questions about PDF files.

The project reads PDFs from `data/pdfs`, extracts their text, splits the text into searchable chunks, stores those chunks in ChromaDB, retrieves the most relevant chunks for a question, and sends that context to a local Ollama model for answer generation.

## What This App Does

This app lets you:

- Put PDF files in `data/pdfs`
- Build a local vector index from those PDFs
- Ask natural-language questions about the indexed documents
- Get an answer generated from retrieved PDF context
- See which PDF, page, and chunk were used as sources

Everything is designed to run locally:

- PDF parsing uses PyMuPDF
- Embeddings use `sentence-transformers`
- Vector search uses ChromaDB
- Answer generation uses Ollama
- The UI uses Streamlit

## Workflow Overview

```text
PDF files
 -> extract page text
 -> clean and chunk text
 -> embed chunks
 -> store chunks in ChromaDB
 -> embed user question
 -> retrieve matching chunks
 -> send context to Ollama
 -> show answer and sources in Streamlit
```

## Project Structure

```text
app/
  ingest/
    pdf_parser.py       Extracts text from PDFs page by page
    chunker.py          Cleans page text and splits it into overlapping chunks

  rag/
    embeddings.py       Loads the embedding model and creates vectors
    vector_store.py     Stores and queries chunks in ChromaDB
    ollama_client.py    Builds prompts and calls the local Ollama API
    pipeline.py         Orchestrates ingestion, retrieval, and answering

  ui/
    streamlit_app.py    Streamlit interface for indexing and asking questions

data/
  pdfs/                 Put your local PDF files here, not committed by default
  chroma/               ChromaDB persistence directory, generated locally

requirements.txt        Python dependencies
```

## How The Files Work Together

### 1. PDF Extraction

`app/ingest/pdf_parser.py`

This file reads PDF files from a directory and extracts text one page at a time.

Each extracted page becomes a dictionary like:

```python
{
    "source": "paper.pdf",
    "path": "data/pdfs/paper.pdf",
    "page": 1,
    "text": "Extracted page text..."
}
```

The main functions are:

- `extract_pdf_pages(pdf_path)`: extracts text from one PDF
- `load_pdfs(pdf_dir)`: loads all `.pdf` files in a directory

### 2. Chunking

`app/ingest/chunker.py`

This file takes extracted pages and splits them into smaller overlapping text chunks.

By default:

- Each chunk is up to `800` characters
- Consecutive chunks overlap by `150` characters

The overlap helps preserve context when useful information sits near a chunk boundary.

Each chunk includes:

- A stable ID
- The chunk text
- Metadata with PDF name, path, page number, and chunk number

Example chunk ID:

```text
paper.pdf::p3::c2
```

That means:

- PDF: `paper.pdf`
- Page: `3`
- Chunk: `2`

### 3. Embeddings

`app/rag/embeddings.py`

This file loads the sentence-transformers model and turns text into vectors.

The current model is:

```text
all-MiniLM-L6-v2
```

The model is cached with `lru_cache`, so it is loaded only once per Python process.

The main function is:

```python
embed_texts(texts)
```

It accepts a list of strings and returns a list of embedding vectors.

### 4. Vector Storage

`app/rag/vector_store.py`

This file manages the local ChromaDB collection.

The current collection is:

```text
pdf_chunks
```

The database is persisted in:

```text
data/chroma
```

The main functions are:

- `get_collection()`: opens or creates the Chroma collection
- `reset_collection()`: deletes and recreates the collection
- `add_chunks(chunks, embeddings)`: stores chunks and embeddings
- `query_chunks(query_embedding, top_k=3)`: retrieves the most similar chunks

Important detail: ingestion currently resets the collection each time. This means pressing "Ingest PDFs" rebuilds the index from the PDFs currently in `data/pdfs`.

### 5. RAG Pipeline

`app/rag/pipeline.py`

This is the orchestration layer. It connects the lower-level modules into complete workflows.

Ingestion flow:

```python
reset_collection()

for pdf_path in pdf_paths:
    pages = extract_pdf_pages(pdf_path)
    chunks = chunk_pages(pages)

    for chunk_batch in _batched(chunks, ingest_batch_size):
        embeddings = embed_texts([chunk["text"] for chunk in chunk_batch])
        add_chunks(chunk_batch, embeddings, reset=False)
```

This keeps peak memory lower because the app processes one PDF and one chunk batch at a time.

Question-answering flow:

```python
query_embedding = embed_texts([question])[0]
chunks = query_chunks(query_embedding, top_k=top_k)
context = format_context(chunks)
answer = generate_answer(question, context)
```

The main functions are:

- `ingest_pdfs(pdf_dir)`: builds the vector index from PDFs
- `answer_question(question, top_k=3)`: retrieves context and asks Ollama
- `index_status()`: returns the number of indexed chunks

### 6. Ollama Client

`app/rag/ollama_client.py`

This file talks to the local Ollama API.

Current settings:

```text
URL:   http://localhost:11434
Model: qwen2.5:0.5b
```

The prompt tells the model to answer using only the retrieved context. If the answer is not present in the provided context, the model is instructed to say:

```text
I don't know based on the provided documents.
```

### 7. Streamlit UI

`app/ui/streamlit_app.py`

This file provides the user interface.

The sidebar shows:

- PDF folder location
- Number of indexed chunks
- "Ingest PDFs" button

The main area provides:

- A question input
- "Ask" button
- Generated answer
- Source list showing PDF, page, and chunk number

## Setup

### 1. Create and activate a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```powershell
pip install -r requirements.txt
```

### 3. Install and run Ollama

Install Ollama from:

```text
https://ollama.com
```

Then pull the model used by this project:

```powershell
ollama pull qwen2.5:0.5b
```

Make sure Ollama is running locally at:

```text
http://localhost:11434
```

### 4. Add PDFs

Put your PDF files in:

```text
data/pdfs
```

### 5. Run the app

From the project root:

```powershell
streamlit run app/ui/streamlit_app.py
```

Then open the Streamlit URL shown in the terminal.

## How To Use

1. Add one or more PDFs to `data/pdfs`.
2. Start the Streamlit app.
3. Click "Ingest PDFs" in the sidebar.
4. Wait for the app to read, chunk, embed, and store the documents.
5. Type a question in the main input.
6. Click "Ask".
7. Read the answer and check the listed sources.

## Current Strengths

- The code is split into clear modules with focused responsibilities.
- The workflow is easy to inspect and modify.
- ChromaDB persists the index locally.
- Source metadata is preserved through the pipeline.
- The app runs without requiring a cloud LLM.
- The prompt is constrained to retrieved document context.

## GitHub Notes

The project is set up to keep local/generated files out of version control:

- `.venv/` and other virtual environments are ignored
- Python caches are ignored
- Streamlit and pytest caches are ignored
- ChromaDB data under `data/chroma/` is ignored
- Local PDFs under `data/pdfs/*.pdf` are ignored
- Environment files such as `.env` are ignored

This matters because PDFs may be large, private, or copyrighted, and ChromaDB indexes are generated artifacts that can be rebuilt locally.

## GPU And Memory Settings

The embedding model automatically uses CUDA when PyTorch can see a compatible local GPU. If CUDA is not available, embeddings fall back to CPU.

You can override the embedding device with:

```powershell
$env:RAG_EMBEDDING_DEVICE = "cuda"
```

or force CPU with:

```powershell
$env:RAG_EMBEDDING_DEVICE = "cpu"
```

You can also reduce embedding RAM usage by lowering the embedding batch size:

```powershell
$env:RAG_EMBEDDING_BATCH_SIZE = "8"
```

The default embedding batch size is `16`.

You can reduce ingestion memory further by lowering the number of chunks processed per storage batch:

```powershell
$env:RAG_INGEST_BATCH_SIZE = "32"
```

The default ingestion batch size is `64`.

Ingestion also processes PDFs and chunk batches incrementally instead of embedding the entire corpus at once. This keeps peak memory lower on machines with limited RAM.

For Ollama, GPU usage is controlled by Ollama and your installed model/runtime, not by this Python code. Make sure your Ollama installation can see your GPU and that the selected model fits your available VRAM.

## Current Limitations

This is a solid early local RAG implementation, but it is not production-grade yet.

Important limitations:

- Chunking is character-based, not sentence-aware or token-aware.
- Chunks can split sentences or paragraphs in awkward places.
- Ingestion rebuilds the whole index every time.
- There is no incremental indexing or file-change detection.
- The default Ollama model, `qwen2.5:0.5b`, is small and may give limited answers.
- Retrieval returns only the top 3 chunks by default.
- The app does not yet support uploaded files through the UI.
- There are no automated tests covering the full workflow yet.

## Good Next Improvements

The best next upgrades would be:

- Add sentence-aware or paragraph-aware chunking
- Add token-based chunk sizing
- Track file hashes to avoid re-indexing unchanged PDFs
- Support incremental add/update/delete indexing
- Make model names and chunk settings configurable
- Add tests for chunking, ingestion, retrieval, and empty-index behavior
- Add richer citations, such as page snippets or character offsets
- Add a PDF upload control in Streamlit

## Troubleshooting

### "No indexed PDF chunks were found"

This means ChromaDB has no stored chunks yet.

Fix:

1. Add PDFs to `data/pdfs`
2. Click "Ingest PDFs"
3. Ask your question again

### Ollama connection error

Make sure Ollama is installed and running.

Check that this URL is available:

```text
http://localhost:11434
```

Also make sure the configured model has been pulled:

```powershell
ollama pull qwen2.5:0.5b
```

### First embedding run is slow

The first run may download the sentence-transformers model. After that, the model should be cached locally.

### Answers are weak or incomplete

Possible causes:

- The relevant content was not extracted cleanly from the PDF
- The relevant text was split across chunks
- The top 3 retrieved chunks did not contain enough context
- The local Ollama model is too small for the question

Useful improvements:

- Increase `top_k`
- Use a stronger Ollama model
- Improve chunking
- Check source chunks to confirm the right context was retrieved

## Mental Model

The app has two separate phases:

### Ingestion

Ingestion prepares the documents.

```text
PDFs -> pages -> chunks -> embeddings -> ChromaDB
```

You run this when PDFs are added or changed.

### Question Answering

Question answering uses the prepared index.

```text
question -> question embedding -> similar chunks -> prompt context -> Ollama answer
```

You run this every time you ask a question.
