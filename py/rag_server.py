import requests
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict, Any, Union
import json
import sqlite3
from datetime import datetime
from fastapi import Body
import os
import time

app = FastAPI()

# Ollama configuration
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "gemma3"  # Using gemma3 which is faster

# Web search configuration (using free SerpAPI)
SERPAPI_KEY = "your_serpapi_key_here"  # Get free key from https://serpapi.com/
USE_WEB_SEARCH = True  # Set to False to disable web search

def search_web_serpapi(query: str) -> str:
    """Search the web using SerpAPI for real-time information"""
    if not SERPAPI_KEY or SERPAPI_KEY == "your_serpapi_key_here":
        return f"Search query: {query} (API key not configured)"
    
    try:
        url = "https://serpapi.com/search"
        params = {
            "q": f"carcinogen risk {query} food safety",
            "api_key": SERPAPI_KEY,
            "num": 3  # Get top 3 results
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Extract snippets from search results
        snippets = []
        if "organic_results" in data:
            for result in data["organic_results"][:3]:
                title = result.get("title", "")
                snippet = result.get("snippet", "")
                link = result.get("link", "")
                snippets.append(f"{title}: {snippet} (Source: {link})")
        
        return "\n".join(snippets) if snippets else f"No web results found for: {query}"
        
    except Exception as e:
        print(f"Web search error: {e}")
        return f"Search query: {query} (search failed)"

def retrieve_context(ingredient: str) -> str:
    """
    Retrieve relevant context documents for an ingredient.
    Now includes real web search!
    """
    if USE_WEB_SEARCH and SERPAPI_KEY != "your_serpapi_key_here":
        # Use real web search
        web_results = search_web_serpapi(ingredient)
        return f"Web search results for {ingredient}:\n{web_results}"
    else:
        # Fallback to static keywords
        context_keywords = {
            "bacon": "processed meat carcinogen WHO Group 1",
            "sausage": "processed meat carcinogen WHO Group 1", 
            "hot dog": "processed meat carcinogen WHO Group 1",
            "artificial colors": "food dyes carcinogen FDA",
            "preservatives": "food preservatives carcinogen risk",
            "nitrites": "nitrites processed meat carcinogen",
            "aspartame": "artificial sweetener aspartame carcinogen",
            "saccharin": "artificial sweetener saccharin carcinogen",
            "BHA": "BHA preservative carcinogen",
            "BHT": "BHT preservative carcinogen"
        }
        
        ingredient_lower = ingredient.lower()
        for keyword, context in context_keywords.items():
            if keyword in ingredient_lower:
                return context
        
        return f"carcinogen risk assessment {ingredient} food safety"

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

@app.post("/ingredients")
def get_llm_response(
    request: Union[IngredientRequest, list[ProductRequest]] = Body(...)
):
    # Helper to process a single analysis
    def analyze_ingredients(ingredients: str):
        cache_key = ",".join(sorted([i.strip().lower() for i in ingredients.split(",") if i.strip()]))
        if cache_key in ingredient_cache:
            result = ingredient_cache[cache_key]
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
        
        ingredient_list = [i.strip() for i in ingredients.split(",") if i.strip()]
        results = []
        
        for ingredient in ingredient_list:
            if not ingredient or ingredient.lower() == "ingredients":
                continue
                
            # Retrieve context for this ingredient
            context = retrieve_context(ingredient)
            
            # Create prompt with context
            prompt = f"""<s>[INST] You are an expert in food safety and carcinogen risk assessment.

Context about {ingredient}: {context}

Analyze the carcinogen risk for: {ingredient}

You must respond with ONLY a valid JSON object in this exact format, no other text:
{{
  "name": "{ingredient}",
  "risk_level": "Low/Medium/High/Unknown",
  "score": 0-100,
  "source": "URL or citation or 'N/A'",
  "explanation": "Brief explanation of the risk assessment"
}}

If there is no known risk, set risk_level to "Low", score to 0, source to "N/A", and explanation to "No known carcinogen risk."

IMPORTANT: Respond ONLY with the JSON object, no additional text, no explanations outside the JSON. [/INST]"""
            
            try:
                # Generate response using Ollama
                payload = {
                    "model": OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False
                }
                
                response = requests.post(OLLAMA_URL, json=payload, timeout=60)
                response.raise_for_status()
                data = response.json()
                llm_output = data.get("response", "").strip()
                
                # Debug: Print what the AI returned
                print(f"AI response for {ingredient}: {llm_output[:500]}...")
                
                # Try to parse JSON from response
                try:
                    # First try direct JSON parsing
                    result = json.loads(llm_output)
                    results.append(result)
                except json.JSONDecodeError:
                    # If that fails, try to extract JSON from the response
                    import re
                    json_match = re.search(r'\{.*\}', llm_output, re.DOTALL)
                    if json_match:
                        try:
                            extracted_json = json_match.group(0)
                            result = json.loads(extracted_json)
                            results.append(result)
                        except json.JSONDecodeError:
                            # If still fails, create a fallback entry
                            results.append({
                                "name": ingredient,
                                "risk_level": "unknown",
                                "score": "unknown", 
                                "source": "N/A",
                                "explanation": f"Unable to parse AI response. Raw response: {llm_output[:200]}..."
                            })
                    else:
                        # No JSON found in response
                        results.append({
                            "name": ingredient,
                            "risk_level": "unknown",
                            "score": "unknown", 
                            "source": "N/A",
                            "explanation": f"AI did not return valid JSON. Raw response: {llm_output[:200]}..."
                        })
                    
            except Exception as e:
                results.append({
                    "name": ingredient,
                    "risk_level": "unknown",
                    "score": "unknown",
                    "source": "N/A", 
                    "explanation": f"Error during analysis: {str(e)}"
                })
        
        # Apply fallback logic
        result = fill_missing_with_known(ingredient_list, results)
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

@app.get("/test")
def test_endpoint():
    """Simple test endpoint to check if backend is running"""
    return {
        "status": "Backend is running!",
        "timestamp": datetime.utcnow().isoformat(),
        "ollama_available": True  # We're using Ollama now
    }

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "model": "ollama",
        "ollama_url": OLLAMA_URL
    } 