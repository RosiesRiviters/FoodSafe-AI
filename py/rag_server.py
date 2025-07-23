import requests
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict, Any, Union
import json
import sqlite3
from datetime import datetime
from fastapi import Body

app = FastAPI()

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "gemma3"  # Change to your preferred model

# Example dictionary of known carcinogen scores
KNOWN_CARCINOGEN_SCORES = {
    "bacon": {
        "risk_level": "High",
        "score": 90,
        "source": "https://www.cancer.org/latest-news/processed-meat-and-cancer-what-you-need-to-know.html",
        "explanation": "Processed meats like bacon are classified as Group 1 carcinogens by the WHO."
    },
    "lettuce": {
        "risk_level": "Low",
        "score": 5,
        "source": "https://www.cancer.org/healthy/eat-healthy-get-active/eat-healthy/vegetables.html",
        "explanation": "Lettuce is not associated with carcinogenic risk."
    },
    # Add more known ingredients as needed
}

def fill_missing_with_known(ingredients: List[str], llm_data: Any) -> List[Dict[str, Any]]:
    """
    Ensures each ingredient has all required keys, using known scores if LLM data is missing or incomplete.
    Always provides a default for missing fields.
    Implements:
    - If ingredient is empty, 'invalid', or not found, all fields are 'unknown'.
    - If score is 0, risk_level is 'unknown'.
    """
    try:
        llm_list = json.loads(llm_data) if isinstance(llm_data, str) else llm_data
    except Exception:
        llm_list = []
    llm_dict = {item.get("name", "").strip().lower(): item for item in llm_list if isinstance(item, dict)}
    result = []
    for ing in ingredients:
        key = ing.strip().lower()
        # Ignore the word 'ingredients' as an ingredient
        if not key or key == "ingredients" or key == "invalid" or key == "invalid name":
            entry = {"name": ing, "risk_level": "unknown", "score": "unknown", "source": "unknown", "explanation": "unknown"}
            result.append(entry)
            continue
        llm_item = llm_dict.get(key, {})
        known = KNOWN_CARCINOGEN_SCORES.get(key, {})
        # If LLM and known are both empty, mark as unknown
        if not llm_item and not known:
            entry = {"name": ing, "risk_level": "unknown", "score": "unknown", "source": "unknown", "explanation": "unknown"}
            result.append(entry)
            continue
        score = llm_item.get("score") or known.get("score", "unknown")
        # If score is 0, set risk_level to 'unknown'
        if score == 0 or score == "0":
            risk_level = "unknown"
        else:
            risk_level = llm_item.get("risk_level") or known.get("risk_level", "unknown")
        entry = {
            "name": ing,
            "risk_level": risk_level,
            "score": score,
            "source": llm_item.get("source") or known.get("source", "unknown"),
            "explanation": llm_item.get("explanation") or known.get("explanation", "unknown"),
        }
        result.append(entry)
    return result

# Initialize SQLite DB and table
DB_PATH = "analysis_log.db"
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS analysis_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        input TEXT,
        result TEXT,
        error TEXT
    )''')
    conn.commit()
    conn.close()
init_db()

def log_analysis(input_str: str, result: str = None, error: str = None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "INSERT INTO analysis_log (timestamp, input, result, error) VALUES (?, ?, ?, ?)",
        (datetime.utcnow().isoformat(), input_str, result, error)
    )
    conn.commit()
    conn.close()

class IngredientRequest(BaseModel):
    ingredients: str  # Accepts a string of comma-separated ingredients

class ProductRequest(BaseModel):
    product: str
    ingredients: str

# Ingredient score cache (in-memory, server lifetime)
ingredient_cache: Dict[str, List[Dict[str, Any]]] = {}

BING_API_KEY = "YOUR_BING_API_KEY"

def get_rag_context(ingredient):
    try:
        return search_web_bing(f"carcinogen risk of {ingredient}", BING_API_KEY)
    except Exception as e:
        return "No web context available."

def analyze_ingredients(ingredients: str):
    ingredient_list = [i.strip() for i in ingredients.split(",") if i.strip()]
    results = []
    for ing in ingredient_list:
        web_context = get_rag_context(ing)
        prompt = (
            f"Ingredient: {ing}\n"
            f"Web search context:\n{web_context}\n"
            "Based on the above, assess the carcinogen risk. "
            "Respond in JSON with keys: name, risk_level, score, source, explanation."
        )
        payload = {
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False
        }
        try:
            response = requests.post(OLLAMA_URL, json=payload)
            response.raise_for_status()
            data = response.json()
            llm_output = data.get("response", "")
            # Try to parse JSON from LLM output
            try:
                result = json.loads(llm_output)
                if isinstance(result, dict):
                    results.append(result)
                else:
                    results.append({"name": ing, "risk_level": "Unknown", "score": "Unknown", "source": "N/A", "explanation": "No valid response from LLM."})
            except Exception:
                results.append({"name": ing, "risk_level": "Unknown", "score": "Unknown", "source": "N/A", "explanation": "No valid response from LLM."})
        except Exception as e:
            results.append({"name": ing, "risk_level": "Unknown", "score": "Unknown", "source": "N/A", "explanation": str(e)})
    return results

@app.post("/ingredients")
def get_llm_response(
    request: Union[IngredientRequest, list[ProductRequest]] = Body(...)
):
    # Helper to process a single analysis
    def analyze_ingredients(ingredients: str):
        cache_key = ",".join(sorted([i.strip().lower() for i in ingredients.split(",") if i.strip()]))
        if cache_key in ingredient_cache:
            result = ingredient_cache[cache_key]
            # Add warning if any score > 80
            high_risk = [item["name"] for item in result if isinstance(item.get("score"), (int, float)) and item["score"] > 80]
            warning = None
            if high_risk:
                warning = f"Warning: High carcinogen risk for: {', '.join(high_risk)}."
            log_analysis(ingredients, json.dumps(result), None)
            response_json = {"ingredients": result}
            if warning:
                response_json["warning"] = warning
            response_json["cached"] = True
            return response_json
        few_shot_example = (
            "Example input: Ingredients: bacon, lettuce\n"
            "Example output: [\n"
            "  {\n"
            "    \"name\": \"bacon\",\n"
            "    \"risk_level\": \"High\",\n"
            "    \"score\": 90,\n"
            "    \"source\": \"https://www.cancer.org/latest-news/processed-meat-and-cancer-what-you-need-to-know.html\",\n"
            "    \"explanation\": \"Processed meats like bacon are classified as Group 1 carcinogens by the WHO.\"\n"
            "  },\n"
            "  {\n"
            "    \"name\": \"lettuce\",\n"
            "    \"risk_level\": \"Low\",\n"
            "    \"score\": 5,\n"
            "    \"source\": \"https://www.cancer.org/healthy/eat-healthy-get-active/eat-healthy/vegetables.html\",\n"
            "    \"explanation\": \"Lettuce is not associated with carcinogenic risk.\"\n"
            "  }\n"
            "]\n"
        )
        prompt = (
            "For each of the following ingredients, assess the carcinogen risk and return a valid JSON array. "
            "Each ingredient should be an object with the following keys: "
            "name (ingredient name), risk_level (Low, Medium, High), score (0-100), source (URL or citation from a reputable organization, or 'N/A' if not available), and explanation (short text). "
            "If there is no known risk, set risk_level to 'Low', score to 0, source to 'N/A', and explanation to 'No known carcinogen risk.' "
            "Respond ONLY with a valid JSON array, no extra text.\n"
            f"{few_shot_example}"
            f"Ingredients: {ingredients}"
        )
        payload = {
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False
        }
        try:
            response = requests.post(OLLAMA_URL, json=payload)
            response.raise_for_status()
            data = response.json()
            llm_output = data.get("response", "[]")
            ingredient_list = [i.strip() for i in ingredients.split(",") if i.strip()]
            result = fill_missing_with_known(ingredient_list, llm_output)
            # Cache the result
            ingredient_cache[cache_key] = result
            # Add warning if any score > 80
            high_risk = [item["name"] for item in result if isinstance(item.get("score"), (int, float)) and item["score"] > 80]
            warning = None
            if high_risk:
                warning = f"Warning: High carcinogen risk for: {', '.join(high_risk)}."
            log_analysis(ingredients, json.dumps(result), None)
            response_json = {"ingredients": result}
            if warning:
                response_json["warning"] = warning
            response_json["cached"] = False
            return response_json
        except Exception as e:
            log_analysis(ingredients, None, str(e))
            return {"error": str(e)}

    # Batch mode: list of products
    if isinstance(request, list):
        batch_results = {}
        for prod in request:
            if not isinstance(prod, dict) and not isinstance(prod, ProductRequest):
                continue
            prod_name = prod["product"] if isinstance(prod, dict) else prod.product
            prod_ingredients = prod["ingredients"] if isinstance(prod, dict) else prod.ingredients
            batch_results[prod_name] = analyze_ingredients(prod_ingredients)
        return batch_results
    # Single mode: one ingredient string
    elif isinstance(request, IngredientRequest):
        return analyze_ingredients(request.ingredients)
    # Fallback: try to parse as dict
    elif isinstance(request, dict) and "ingredients" in request:
        return analyze_ingredients(request["ingredients"])
    else:
        return {"error": "Invalid request format."} 

import requests

def search_web_bing(query, api_key):
    url = "https://api.bing.microsoft.com/v7.0/search"
    headers = {"Ocp-Apim-Subscription-Key": api_key}
    params = {"q": query, "textDecorations": True, "textFormat": "HTML", "count": 3}
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    results = response.json()
    snippets = []
    for web_page in results.get("webPages", {}).get("value", []):
        snippets.append(f"{web_page['name']}: {web_page['snippet']} (Source: {web_page['url']})")
    return "\n".join(snippets) 