# Minimal RAG Backend with Llama (Python)

## Setup

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Run the FastAPI server:

```bash
uvicorn rag_server:app --reload
```

3. Test the endpoint (example with curl):

```bash
curl -X POST "http://127.0.0.1:8000/rag" -H "Content-Type: application/json" -d '{"query": "What is RAG?", "context": []}'
```

## Next Steps
- Integrate Llama model loading and inference in `rag_server.py`.
- Add retrieval logic for context documents.
- Connect this backend to your Next.js frontend. 