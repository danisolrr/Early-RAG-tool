import requests


OLLAMA_URL = "http://localhost:11434"
OLLAMA_MODEL = "qwen2.5:0.5b"


def build_prompt(question: str, context: str) -> str:
    return f"""Answer the question using ONLY the context below.
If the context does not contain the answer, say: I don't know based on the provided documents.

Context:
{context}

Question: {question}

Answer:"""


def generate_answer(
    question: str,
    context: str,
    base_url: str = OLLAMA_URL,
    model: str = OLLAMA_MODEL,
) -> str:
    response = requests.post(
        f"{base_url.rstrip('/')}/api/generate",
        json={
            "model": model,
            "prompt": build_prompt(question, context),
            "stream": False,
            "options": {
                "temperature": 0.0,
            },
        },
        timeout=120,
    )
    response.raise_for_status()
    data = response.json()
    return data.get("response", "").strip()
