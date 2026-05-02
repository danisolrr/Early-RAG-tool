import sys
from pathlib import Path

import streamlit as st


ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.rag.pipeline import PDF_DIR, answer_question, index_status, ingest_pdfs


st.set_page_config(page_title="Local PDF RAG", page_icon="L", layout="wide")

st.title("Local PDF RAG")
st.caption("PyMuPDF + sentence-transformers + ChromaDB + Ollama")

PDF_DIR.mkdir(parents=True, exist_ok=True)

with st.sidebar:
    st.header("Index")
    st.write(f"PDF folder: `{PDF_DIR}`")
    status = index_status()
    st.metric("Indexed chunks", status["chunks"])

    if st.button("Ingest PDFs", type="primary", use_container_width=True):
        with st.spinner("Reading PDFs, chunking, embedding, and storing in Chroma..."):
            try:
                result = ingest_pdfs(PDF_DIR)
            except Exception as exc:
                st.error(f"Ingestion failed: {exc}")
            else:
                st.success(
                    f"Indexed {result['chunks']} chunks from "
                    f"{result['pages']} pages across {result['pdfs']} PDFs."
                )
                st.rerun()

question = st.text_input("Question", placeholder="Ask something from your PDFs")

if st.button("Ask", disabled=not question.strip()):
    with st.spinner("Retrieving context and asking Ollama..."):
        try:
            result = answer_question(question.strip(), top_k=3)
        except Exception as exc:
            st.error(f"Answer generation failed: {exc}")
        else:
            st.subheader("Answer")
            st.write(result["answer"])

            st.subheader("Sources")
            if result["sources"]:
                for source in result["sources"]:
                    st.write(
                        f"- {source['source']} - page {source['page']}, "
                        f"chunk {source['chunk']}"
                    )
            else:
                st.write("No sources found.")
