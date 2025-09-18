# Minimal Backend with OpenAI (Python)

## Setup

1. Set environment variables (create `py/.env`):

```
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
USE_WEB_SEARCH=true
SERPAPI_KEY=your_serpapi_key
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run the FastAPI server:

```bash
uvicorn rag_server:app --reload
```

4. Test the endpoint (example with curl):

```bash
curl -X POST "http://127.0.0.1:8000/rag" -H "Content-Type: application/json" -d '{"query": "What is RAG?", "context": []}'
```

## Notes
- Uses OpenAI Chat Completions with JSON mode.
- Optional real-time web search via SerpAPI for context retrieval.