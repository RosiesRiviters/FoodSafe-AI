import requests
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List

app = FastAPI()

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "gemma3"

class RAGRequest(BaseModel):
    query: str
    context: List[str] = []

@app.post("/rag")
def rag_endpoint(request: RAGRequest):
    # Combine context and query for RAG (simple concat for now)
    prompt = "\n".join(request.context + [request.query])
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False
    }
    try:
        response = requests.post(OLLAMA_URL, json=payload)
        response.raise_for_status()
        data = response.json()
        return {"answer": data.get("response", "No response from Ollama.")}
    except Exception as e:
        return {"error": str(e)} 