# FoodSafe AI

## Quick Start

### Prerequisites
- Python 3.8+
- Node.js 18+
- [Ollama](https://ollama.com/) installed and running locally (e.g., `ollama serve`)
- (Optional) Pull your desired Ollama model, e.g.:
  ```sh
  ollama pull gemma3
  ```

### 1. Start the Backend (FastAPI)
From the project root:
```sh
pip install fastapi uvicorn requests
uvicorn app:app --reload
```

### 2. Start the Frontend (Next.js)
In a new terminal, from the project root:
```sh
npm install
npm run dev
```

### 3. Open the App
Visit [http://localhost:3000](http://localhost:3000) in your browser.

---

## Features
- Analyze carcinogen risk for food ingredients using a local LLM (Ollama)
- Batch mode: analyze multiple products at once
- Caching and logging for efficiency and traceability
- Warnings for high-risk ingredients

---

## Troubleshooting
- Make sure Ollama is running and the model is available
- The backend runs on port 8000, the frontend on 3000
- Logs are stored in `analysis_log.db`

---

For more details, see the rest of this README and the `docs/` folder.

ollama serve

---

## How to Fix

### 1. Install Node.js

- **Recommended:** Download and install from the [official Node.js website](https://nodejs.org/).
  - Choose the LTS version.
- **Or, with Homebrew (on Mac):**
  ```sh
  brew install node
  ```

### 2. Verify Installation

After installation, run:
```sh
node -v
npm -v
```
You should see version numbers for both.

### 3. Try Again

Now, from your project root:
```sh
npm install
npm run dev
```

---

**If you run into any issues during installation, let me know what you see!**  
Once Node.js and npm are working, your frontend will start up as expected.

---

## Option 1: Official Node.js Installer (Recommended)

1. Go to the [official Node.js download page](https://nodejs.org/).
2. Download the **macOS Installer** (choose the LTS version).
3. Open the downloaded `.pkg` file and follow the installation instructions.
4. After installation, open a new terminal and run:
   ```sh
   node -v
   npm -v
   ```
   You should see version numbers for both.

---

## Option 2: Using Anaconda (if you use conda)

If you use Anaconda/Miniconda, you can install Node.js in your environment:
```sh
conda install -c conda-forge nodejs
```
Then verify with:
```sh
node -v
npm -v
```

---

## Option 3: Node Version Manager (nvm)

If you want to manage multiple Node.js versions, you can use [nvm](https://github.com/nvm-sh/nvm):

1. Install nvm:
   ```sh
   curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
   ```
2. Restart your terminal, then run:
   ```sh
   nvm install --lts
   nvm use --lts
   node -v
   npm -v
   ```

---

**Let me know which method you prefer, or if you need step-by-step help with any of them!**

---

## 1. Ollama Server Not Running

**Solution:**  
Open a terminal and run:
```sh
ollama serve
```
Leave this terminal open.  
You should see output like:
```
Ollama server listening on 11434...
```

---

## 2. Model Not Pulled or Loaded

**Solution:**  
Make sure you have pulled the model you want to use (e.g., gemma3, llama2, etc.):
```sh
ollama pull gemma3
```
(Replace `gemma3` with your desired model.)

---

## 3. Backend Cannot Reach Ollama

- Your FastAPI backend (`py/rag_server.py`) is configured to POST to `http://localhost:11434/api/generate`.
- If Ollama is not running, or is running on a different port, or you have a firewall issue, the backend will fail to connect.

**Test Ollama API directly:**  
In a terminal, run:
```sh
curl http://localhost:11434
```
You should get a response (even if it’s an error message).

---

## 4. Model Name Mismatch

- In your backend code, check this line:
  ```python
  OLLAMA_MODEL = "gemma3"
  ```
- If you pulled a different model, update this to match the model name you pulled.

---

## 5. Error Messages

- If you see errors in your backend terminal like “connection refused” or “model not found,” please copy and paste the full error message here for more specific help.

---

## 6. Backend Logs

- Check the terminal where you run `python -m uvicorn py.rag_server:app --reload` for any error messages when you make a request from the frontend.

---

## 7. Example: Test the Backend Directly

Try this in a terminal:
```sh
curl -X POST "http://localhost:8000/ingredients" -H "Content-Type: application/json" -d '{"ingredients": "bacon, lettuce"}'
```
- If you get an error, paste it here.

---

## Summary Checklist

- [ ] Is `ollama serve` running?
- [ ] Did you pull the model you want to use?
- [ ] Is the model name in your backend code correct?
- [ ] Can you reach `http://localhost:11434` from your terminal?
- [ ] Do you see errors in your backend terminal?

---

**If you’re still stuck, please tell me:**
- What error do you see in the backend terminal?
- What is the output of `curl http://localhost:11434`?
- What is the output of the backend test curl above?

I’ll help you fix it step by step!

---

Absolutely! The "fetch failed" error when entering ingredients usually means your frontend could not reach the backend, or the backend could not reach Ollama. Here’s how to debug and fix it step by step:

---

## 1. Check the Backend Terminal

When you submit ingredients in the web UI, look at the terminal where you ran:
```sh
python -m uvicorn py.rag_server:app --reload
```
- **Do you see any error messages?**
- If yes, please copy and paste the error here.

---

## 2. Test the Backend Directly

Open a new terminal and run:
```sh
curl -X POST "http://localhost:8000/ingredients" -H "Content-Type: application/json" -d '{"ingredients": "bacon, lettuce"}'
```
- **Do you get a JSON response, or an error?**
- If you get an error, paste it here.

---

## 3. Test Ollama Directly

Open a new terminal and run:
```sh
curl http://localhost:11434
```
- **Do you get a response?** (Even an error message is OK; it means the server is up.)
- If you get “connection refused” or no response, Ollama is not running.

---

## 4. Common Issues & Fixes

### A. Ollama Not Running
- Make sure you have a terminal running:
  ```sh
  ollama serve
  ```

### B. Backend Not Running
- Make sure you have a terminal running:
  ```sh
  python -m uvicorn py.rag_server:app --reload
  ```

### C. Port or Firewall Issues
- Make sure nothing else is using port 8000 (backend) or 11434 (Ollama).
- Make sure you are not running in a restricted network environment.

### D. Model Name Mismatch
- In `py/rag_server.py`, make sure:
  ```python
  OLLAMA_MODEL = "gemma3"
  ```
  matches the model you pulled with `ollama pull`.

---

## 5. Check the Browser Console

- Open your browser’s developer tools (F12 or right-click → Inspect → Console/Network).
- Try submitting ingredients again.
- **Do you see a network error or a specific error message?**  
  (Paste it here if you do.)

---

## 6. Summary Checklist

- [ ] Is `ollama serve` running?
- [ ] Did you pull the model and is the model name correct?
- [ ] Is the backend running with no errors?
- [ ] Does `curl http://localhost:11434` work?
- [ ] Does `curl -X POST "http://localhost:8000/ingredients" ...` work?
- [ ] Any errors in the browser console or backend terminal?

---

**Please try the steps above and paste any error messages you see. I’ll help you fix it right away!**

---

**You want:**  
A website where you enter any ingredients, and it uses a local Ollama model to output carcinogen risks—no complicated setup, just a working demo.

---

## Here’s the Simplest Working Setup

### 1. What You Need

- **Ollama** running locally (`ollama serve`)
- **A FastAPI backend** that talks to Ollama
- **A simple frontend** (React/Next.js or even plain HTML/JS) that talks to the backend

---

### 2. Minimal Working Example

#### **A. Backend (FastAPI, single file, e.g. `app.py`):**

```python
from fastapi import FastAPI
from pydantic import BaseModel
import requests

app = FastAPI()

class IngredientsRequest(BaseModel):
    ingredients: str

@app.post("/analyze")
def analyze(request: IngredientsRequest):
    prompt = f"Assess the carcinogen risk for these ingredients: {request.ingredients}. Respond in JSON."
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={"model": "gemma3", "prompt": prompt, "stream": False}
    )
    return response.json()
```

**Run it:**
```sh
pip install fastapi uvicorn requests
uvicorn app:app --reload
```

---

#### **B. Frontend (Super Simple HTML/JS):**

Create a file called `index.html`:

```html
<!DOCTYPE html>
<html>
<head>
  <title>Carcinogen Risk Checker</title>
</head>
<body>
  <h1>Carcinogen Risk Checker</h1>
  <input id="ingredients" placeholder="Enter ingredients, e.g. bacon, lettuce" size="50"/>
  <button onclick="analyze()">Analyze</button>
  <pre id="result"></pre>
  <script>
    async function analyze() {
      const ingredients = document.getElementById('ingredients').value;
      const res = await fetch('http://localhost:8000/analyze', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ingredients})
      });
      document.getElementById('result').textContent = await res.text();
    }
  </script>
</body>
</html>
```

**Open this file in your browser.**

---

### 3. Make Sure Ollama is Running

```sh
ollama serve
ollama pull gemma3
```

---

### 4. How to Use

1. Start Ollama: `ollama serve`
2. Start backend: `uvicorn app:app --reload`
3. Open `index.html` in your browser
4. Enter ingredients, click Analyze, see results!

---

**This is the absolute minimum setup.**  
If you want this in your Next.js app, I can help you wire it up, but the above will work for demo/testing and is easy to debug.

---

**If you want, I can generate a single zip file with all the code you need. Just say the word!**  
Let me know if you want to stick with this minimal approach or integrate into your existing Next.js project.

---

## 1. Why Does This Happen?

- **LLMs like Ollama** do not actually “search the web” in real time. They generate answers based on their training data and the prompt you give them.
- If the model doesn’t “know” about an ingredient, or if the prompt isn’t clear enough, it may return incomplete or generic results.
- The “source” field is often hallucinated (made up) by the LLM unless you provide it with real data or retrieval-augmented generation (RAG).

---

## 2. How to Improve Results

### A. Make the Prompt More Explicit

You can update your prompt to:
- Ask the model to always provide a score, even if it’s “0” for unknown/harmless ingredients.
- Ask for a real, reputable source (e.g., from WHO, FDA, or a scientific paper), or to say “N/A” if none is available.
- Optionally, instruct the model to say “No known risk” for common foods like tomato.

**Example prompt update:**
```
For each of the following ingredients, assess the carcinogen risk and return a valid JSON array.
Each ingredient should be an object with the following keys:
- name (ingredient name)
- risk_level (Low, Medium, High)
- score (0-100)
- source (URL or citation from a reputable organization, or 'N/A' if not available)
- explanation (short text)

If there is no known risk, set risk_level to 'Low', score to 0, source to 'N/A', and explanation to 'No known carcinogen risk.'

Respond ONLY with a valid JSON array, no extra text.
```

### B. Add a Fallback in Your Backend

If the model returns an invalid or missing score/source, your backend can:
- Set the score to 0 and source to “N/A” for unknown ingredients.
- Always ensure the output is valid and complete.

### C. True Web Search (Advanced)

If you want **real-time sources**, you’d need to:
- Integrate a web search API (e.g., Bing, Google Custom Search, or a scientific database).
- Use RAG (retrieval-augmented generation) to fetch real documents and pass them to the LLM.

This is more complex, but possible if you want to go further.

---

## 3. Example: Improved Backend Fallback

Update your backend’s `fill_missing_with_known` function to always provide a default for missing fields:

```python
entry = {
    "name": ing,
    "risk_level": llm_item.get("risk_level") or known.get("risk_level", "Low"),
    "score": llm_item.get("score") or known.get("score", 0),
    "source": llm_item.get("source") or known.get("source", "N/A"),
    "explanation": llm_item.get("explanation") or known.get("explanation", "No known carcinogen risk."),
}
```

---

## 4. What You Should Do Next

- **Update your prompt** as above for better LLM output.
- **Update your backend fallback** to always provide a valid score/source.
- If you want real sources, consider integrating a web search API (let me know if you want help with this).

---

**Would you like me to update your backend and prompt for you, or help you add real-time web search?**  
Let me know your preference!

Great observation! This is a common limitation of LLMs when:
- The ingredient is not in your known dictionary.
- The LLM doesn’t have enough context or knowledge to assign a risk or source.
- The prompt is not specific enough, or the model is not specialized for food safety.

### Here’s how to improve results:

---

## 1. Expand the Known Carcinogen Dictionary

Add more common processed food ingredients and their risks to your `KNOWN_CARCINOGEN_SCORES` dictionary.  
For example, for boxed mac and cheese, you might add:

```python
KNOWN_CARCINOGEN_SCORES = {
    "bacon": {...},
    "lettuce": {...},
    "yellow 5": {
        "risk_level": "Medium",
        "score": 60,
        "source": "https://www.cancer.org/healthy/eat-healthy/get-active/eat-healthy/food-additives.html",
        "explanation": "Some food dyes like Yellow 5 have been studied for potential health risks."
    },
    "sodium phosphate": {
        "risk_level": "Medium",
        "score": 50,
        "source": "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6024559/",
        "explanation": "Phosphate additives may be linked to health risks when consumed in excess."
    },
    "artificial flavors": {
        "risk_level": "Low",
        "score": 10,
        "source": "https://www.fda.gov/food/food-additives-petitions/overview-food-ingredients-additives-colors",
        "explanation": "Artificial flavors are generally recognized as safe but may cause reactions in sensitive individuals."
    },
    # ...add more as needed
}
```

---

## 2. Make the Prompt More Analytical

Update your prompt to ask the LLM to:
- Consider the risks of food additives, preservatives, and artificial colors.
- Reference scientific or regulatory sources if possible.

**Example:**
```
For each of the following ingredients, assess the carcinogen risk, especially for food additives, preservatives, and artificial colors. Use scientific or regulatory sources if available. If no risk is known, set risk_level to 'Low', score to 0, source to 'N/A', and explanation to 'No known carcinogen risk.' Respond ONLY with a valid JSON array, no extra text.
```

---

## 3. Consider Using a Specialized Model or RAG

- General LLMs may not have up-to-date or detailed food safety knowledge.
- For best results, use a retrieval-augmented generation (RAG) system that can look up real data, or use a model fine-tuned for food safety.

---

## 4. Backend Fallback

Your backend already ensures a valid response, but if you want to avoid “all 0s” for
