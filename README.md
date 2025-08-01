# FoodSafe AI

## Quick Start

### Prerequisites
- Python 3.8+
- Node.js 18+
- At least 8GB RAM (for Llama model)
- 4GB+ free disk space (for model file)

### 1. Download Llama Model

First, download a GGUF format Llama model:

```sh
# Create models directory
mkdir -p py/models

# Download Llama-2-7B-Chat model (recommended)
wget https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF/resolve/main/llama-2-7b-chat.Q4_K_M.gguf -O py/models/llama-2-7b-chat.gguf

# Alternative: Download a smaller model if you have limited RAM
# wget https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF/resolve/main/llama-2-7b-chat.Q5_K_M.gguf -O py/models/llama-2-7b-chat.gguf
```

**Note**: The model file is ~4GB. If you have limited RAM, use a quantized version (Q4_K_M or Q5_K_M).

### 2. Install Python Dependencies

```sh
cd py
pip install -r requirements.txt
```

**Requirements include:**
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `requests` - HTTP client
- `pydantic` - Data validation
- `llama-cpp-python` - Llama model inference
- `sqlite3` - Database (built-in)

### 3. Install Node.js Dependencies

```sh
npm install
```

### 4. Start the Backend (Llama + FastAPI)

From the project root:
```sh
cd py
python -m uvicorn rag_server:app --reload --host 0.0.0.0 --port 8000
```

**Expected output:**
```
✅ Llama model loaded from py/models/llama-2-7b-chat.gguf
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 5. Start the Frontend (Next.js)

In a new terminal, from the project root:
```sh
npm run dev
```

**Expected output:**
```
- ready started server on 0.0.0.0:3000
```

### 6. Open the App

Visit [http://localhost:3000](http://localhost:3000) in your browser.

---

## Features

- **Direct Llama inference** - No external API dependencies
- **Context-aware analysis** - Ingredient-specific knowledge retrieval
- **Batch processing** - Analyze multiple products at once
- **Real-time risk assessment** - Carcinogen risk scoring (0-100)
- **Structured responses** - JSON output with risk levels, sources, explanations
- **Caching system** - Faster repeated queries
- **Health monitoring** - Backend status checks
- **SQLite logging** - Request/response tracking

---

## Model Configuration

### Supported Models
- **Llama-2-7B-Chat** (recommended)
- **Llama-2-13B-Chat** (better quality, more RAM required)
- **CodeLlama** (good for structured outputs)

### Model Path
Update the model path in `py/rag_server.py`:
```python
MODEL_PATH = "models/your-model-name.gguf"
```

### Performance Tuning
Adjust these parameters in `py/rag_server.py`:
```python
LLAMA_MODEL = Llama(
    model_path=MODEL_PATH,
    n_ctx=2048,        # Context window size
    n_threads=4,       # CPU threads (increase for better performance)
    verbose=False
)
```

---

## API Endpoints

### Health Check
```sh
curl http://localhost:8000/health
```

### Single Ingredient Analysis
```sh
curl -X POST "http://localhost:8000/ingredients" \
  -H "Content-Type: application/json" \
  -d '{"ingredients": "bacon, lettuce, tomato"}'
```

### Batch Product Analysis
```sh
curl -X POST "http://localhost:8000/ingredients" \
  -H "Content-Type: application/json" \
  -d '[
    {"product": "BLT", "ingredients": "bacon, lettuce, tomato"},
    {"product": "Mac and Cheese", "ingredients": "pasta, cheese, artificial colors"}
  ]'
```

---

## Troubleshooting

### Model Loading Issues
- **"Model not found"**: Check the `MODEL_PATH` in `rag_server.py`
- **"Out of memory"**: Use a smaller quantized model (Q4_K_M)
- **Slow loading**: The model loads once on startup, subsequent requests are fast

### Backend Issues
- **Port 8000 in use**: Change the port in the uvicorn command
- **Model not responding**: Check the health endpoint `/health`
- **Memory issues**: Reduce `n_threads` or use a smaller model

### Frontend Issues
- **"Connection refused"**: Make sure the backend is running on port 8000
- **"Fetch failed"**: Check browser console for CORS issues

### Performance Tips
- **First request slow**: Normal, model needs to warm up
- **Subsequent requests fast**: Thanks to caching
- **Batch processing**: More efficient than individual requests

---

## Development

### Adding New Ingredients
Update the context keywords in `py/rag_server.py`:
```python
context_keywords = {
    "your_ingredient": "relevant context information",
    # ... existing keywords
}
```

### Customizing the Prompt
Modify the prompt template in the `analyze_ingredients` function to change how the model responds.

### Logging
All requests are logged to `py/analysis_log.db`. View with:
```sh
sqlite3 py/analysis_log.db "SELECT * FROM analysis_log ORDER BY timestamp DESC LIMIT 10;"
```

---

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Next.js UI    │───▶│  FastAPI Backend│───▶│   Llama Model   │
│   (Port 3000)   │    │   (Port 8000)   │    │   (Local)       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   SQLite Logs   │
                       │   (analysis_log.db) │
                       └─────────────────┘
```

---

For more details, see the `docs/` folder and individual component READMEs.
