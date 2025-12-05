# FoodSafe AI

## Quick Start

### Prerequisites
- Python 3.8+
- Node.js 18+
- OpenAI API key (get one from https://platform.openai.com/api-keys)
- Optional: SerpAPI key for enhanced web search (get one from https://serpapi.com/)

### 1. Environment Configuration

Create a `.env` file in the `py/` directory with your API keys:

```sh
cd py
cp .env.example .env  # If .env.example exists, or create manually
```

Required environment variables:
```env
# Required: OpenAI API Key
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini

# Optional: Web Search (for enhanced research)
SERPAPI_KEY=your_serpapi_key_here
USE_WEB_SEARCH=true

# Optional: USDA FoodData Central API
USDA_API_KEY=your_usda_api_key_here
```

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
- `openai` - OpenAI API client
- `python-dotenv` - Environment variable management
- `sqlite3` - Database (built-in)

### 3. Install Node.js Dependencies

```sh
npm install
```

### 4. Start the Backend (FastAPI + OpenAI)

From the project root:
```sh
cd py
python -m uvicorn rag_server:app --reload --host 0.0.0.0 --port 8002
```

**Expected output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8002
INFO:     Application startup complete.
```

**Note**: The backend runs on port 8002 (not 8000) to match the frontend configuration.

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

- **AI-Powered Analysis** - Uses OpenAI GPT models for comprehensive risk assessment
- **Multi-Source Research** - Integrates USDA, OpenFoodFacts, and web search for accurate data
- **Context-aware analysis** - Ingredient-specific knowledge retrieval with component breakdown
- **Batch processing** - Analyze multiple products at once
- **Real-time risk assessment** - Carcinogen risk scoring (0-100)
- **NOVA Classification** - Food processing level classification (1-4)
- **Structured responses** - JSON output with risk levels, sources, explanations
- **Input validation** - Validates that inputs are food products
- **Caching system** - Faster repeated queries
- **Health monitoring** - Backend status checks
- **SQLite logging** - Request/response tracking

---

## Configuration

### OpenAI Model
The default model is `gpt-4o-mini`. You can change it in your `.env` file:
```env
OPENAI_MODEL=gpt-4o-mini  # or gpt-4, gpt-3.5-turbo, etc.
```

### Web Search (Optional)
Enable enhanced web search by setting `USE_WEB_SEARCH=true` and providing a `SERPAPI_KEY` in your `.env` file. This provides more comprehensive research data for risk assessment.

### API Keys
- **OpenAI API Key** (Required): Get from https://platform.openai.com/api-keys
- **SerpAPI Key** (Optional): Get from https://serpapi.com/ for enhanced web search
- **USDA API Key** (Optional): Get from https://fdc.nal.usda.gov/api-guide.html

---

## API Endpoints

### Health Check
```sh
curl http://localhost:8002/health
```

### Single Ingredient Analysis
```sh
curl -X POST "http://localhost:8002/ingredients" \
  -H "Content-Type: application/json" \
  -d '{"ingredients": "bacon, lettuce, tomato"}'
```

### Batch Product Analysis
```sh
curl -X POST "http://localhost:8002/ingredients" \
  -H "Content-Type: application/json" \
  -d '[
    {"product": "BLT", "ingredients": "bacon, lettuce, tomato"},
    {"product": "Mac and Cheese", "ingredients": "pasta, cheese, artificial colors"}
  ]'
```

---

## Troubleshooting

### Backend Issues
- **"OPENAI_API_KEY is not configured"**: Make sure you've created a `.env` file in the `py/` directory with your OpenAI API key
- **Port 8002 in use**: Change the port in the uvicorn command and update the frontend `actions.ts` file
- **API errors**: Check that your OpenAI API key is valid and has credits
- **Web search not working**: Verify your SerpAPI key is set correctly, or set `USE_WEB_SEARCH=false` to disable

### Frontend Issues
- **"Connection refused"**: Make sure the backend is running on port 8002
- **"Fetch failed"**: Check browser console for CORS issues or verify backend is running

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
│   Next.js UI    │───▶│  FastAPI Backend│───▶│   OpenAI API    │
│   (Port 3000)   │    │   (Port 8002)   │    │   (Cloud)       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ├──▶ USDA API
                              ├──▶ OpenFoodFacts API
                              ├──▶ SerpAPI (Web Search)
                              │
                              ▼
                       ┌─────────────────┐
                       │   SQLite Logs   │
                       │   (analysis_log.db) │
                       └─────────────────┘
```

---

For more details, see the `docs/` folder and individual component READMEs.
