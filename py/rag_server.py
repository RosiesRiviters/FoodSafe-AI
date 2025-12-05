import requests
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Union
import json
import sqlite3
from datetime import datetime
from fastapi import Body
import os
import time
from dotenv import load_dotenv
from openai import OpenAI
from pathlib import Path

_dotenv_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=str(_dotenv_path))

app = FastAPI()

# CORS: allow local Next.js dev servers and production Vercel deployment
allowed_origins = [
    "http://localhost:300",
    "http://127.0.0.1:300",
    "http://localhost:3001",
    "http://127.0.0.1:3001",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=r"https://.*\.vercel\.app",  # Allow all Vercel deployments
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# OpenAI configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
openai_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

# Web search configuration (using free SerpAPI)
SERPAPI_KEY = os.getenv("SERPAPI_KEY", "your_serpapi_key_here")  # Get free key from serpapi.com
USE_WEB_SEARCH = os.getenv("USE_WEB_SEARCH", "true").lower() == "true"  # Set to False to disable web search

# USDA FoodData Central API configuration
USDA_API_KEY = os.getenv("USDA_API_KEY", "fhZeMx79vAT18sFJB27zejHGovU5CyV984JdowXf")
USDA_BASE_URL = "https://api.nal.usda.gov/fdc/v1"

# OpenFoodFacts API configuration (open database, no API key needed)
OPENFOODFACTS_BASE_URL = "https://world.openfoodfacts.org/api/v2"
OPENFOODFACTS_SEARCH_URL = "https://world.openfoodfacts.org/cgi/search.pl"

def search_web_serpapi(query: str, search_type: str = "general") -> str:
    """Enhanced web search using SerpAPI for comprehensive real-time information"""
    if not SERPAPI_KEY or SERPAPI_KEY == "your_serpapi_key_here":
        return f"Search query: {query} (API key not configured)"
    
    try:
        url = "https://serpapi.com/search"
        params = {
            "q": query,
            "api_key": SERPAPI_KEY,
            "num": 10,  # Get top 10 results for comprehensive coverage
            "hl": "en",
            "gl": "us"
        }
        
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        # Enhanced result extraction with more detail
        results = []
        
        # Extract organic results
        if "organic_results" in data:
            for i, result in enumerate(data["organic_results"][:8]):
                title = result.get("title", "")
                snippet = result.get("snippet", "")
                link = result.get("link", "")
                
                # Get additional snippet data if available
                rich_snippet = result.get("rich_snippet", {})
                if rich_snippet:
                    snippet += f" | Additional info: {rich_snippet.get('top', {}).get('detected_extensions', '')}"
                
                results.append(f"[{i+1}] {title}\n   Summary: {snippet}\n   Source: {link}")
        
        # Extract knowledge graph if available (for authoritative info)
        if "knowledge_graph" in data:
            kg = data["knowledge_graph"]
            title = kg.get("title", "")
            description = kg.get("description", "")
            if title and description:
                results.insert(0, f"[AUTHORITATIVE] {title}: {description}")
        
        # Extract answer box if available (for direct answers)
        if "answer_box" in data:
            answer = data["answer_box"]
            answer_text = answer.get("answer", "") or answer.get("snippet", "")
            if answer_text:
                results.insert(0, f"[DIRECT ANSWER] {answer_text}")
        
        # Extract related questions for additional context
        if "related_questions" in data:
            related = data["related_questions"][:3]  # Top 3 related questions
            for rq in related:
                question = rq.get("question", "")
                snippet = rq.get("snippet", "")
                if question and snippet:
                    results.append(f"[RELATED] Q: {question} A: {snippet}")
        
        # Extract news results if searching for recent information
        if "news_results" in data and search_type == "recent":
            for news in data["news_results"][:3]:
                title = news.get("title", "")
                snippet = news.get("snippet", "")
                date = news.get("date", "")
                source = news.get("source", "")
                results.append(f"[NEWS {date}] {source}: {title} - {snippet}")
        
        return "\n\n".join(results) if results else f"No comprehensive results found for: {query}"
        
    except Exception as e:
        print(f"Enhanced web search error for '{query}': {e}")
        return f"Search query: {query} (enhanced search failed: {str(e)})"

def perform_multi_angle_search(component: str) -> str:
    """Perform multiple targeted searches for comprehensive component analysis"""
    searches = [
        (f"{component} carcinogen cancer risk studies", "health"),
        (f"{component} toxicity safety data sheet health effects", "safety"),
        (f"{component} WHO IARC classification carcinogenic", "official"),
        (f"{component} food additive safety FDA approval", "regulatory"),
        (f'"{component}" health risks recent studies 2023 2024', "recent")
    ]
    
    all_results = []
    for search_query, search_type in searches:
        print(f"Searching: {search_query}")
        result = search_web_serpapi(search_query, search_type)
        if result and "api key not configured" not in result.lower():
            all_results.append(f"=== {search_type.upper()} RESEARCH ===\n{result}")
    
    return "\n\n".join(all_results) if all_results else f"No detailed research available for {component}"

def search_usda_foods(food_name: str) -> dict:
    """Search USDA FoodData Central for food items"""
    try:
        url = f"{USDA_BASE_URL}/foods/search"
        params = {
            "query": food_name,
            "api_key": USDA_API_KEY,
            "pageSize": 5,  # Get top 5 matches
            "sortBy": "score",
            "sortOrder": "desc"
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        return data
        
    except Exception as e:
        print(f"USDA search error for '{food_name}': {e}")
        return {"foods": [], "error": str(e)}

def get_usda_food_details(fdc_id: str) -> dict:
    """Get detailed information about a specific food from USDA database"""
    try:
        url = f"{USDA_BASE_URL}/food/{fdc_id}"
        params = {
            "api_key": USDA_API_KEY,
            "format": "full"  # Get full details including nutrients and ingredients
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        return data
        
    except Exception as e:
        print(f"USDA details error for FDC ID '{fdc_id}': {e}")
        return {"error": str(e)}

def analyze_usda_food_data(food_name: str) -> str:
    """Comprehensive analysis of food using USDA database"""
    print(f"Searching USDA database for: {food_name}")
    
    # Search for the food
    search_results = search_usda_foods(food_name)
    
    if "error" in search_results or not search_results.get("foods"):
        return f"No USDA data found for '{food_name}' - {search_results.get('error', 'No results')}"
    
    # Get detailed info for the best match
    best_match = search_results["foods"][0]
    fdc_id = best_match.get("fdcId")
    food_description = best_match.get("description", food_name)
    
    print(f"Found USDA match: {food_description} (ID: {fdc_id})")
    
    detailed_data = get_usda_food_details(str(fdc_id))
    
    if "error" in detailed_data:
        return f"Error getting details for '{food_description}': {detailed_data['error']}"
    
    # Extract comprehensive information
    analysis = {
        "food_name": food_description,
        "fdc_id": fdc_id,
        "ingredients": [],
        "nutrients": [],
        "additives": [],
        "concerning_components": []
    }
    
    # Extract ingredients list
    if "ingredients" in detailed_data:
        ingredients_text = detailed_data["ingredients"]
        analysis["ingredients"] = [ing.strip() for ing in ingredients_text.split(",") if ing.strip()]
    
    # Extract food additives/components of concern
    if "foodComponents" in detailed_data:
        for component in detailed_data["foodComponents"]:
            name = component.get("name", "")
            if any(keyword in name.lower() for keyword in ["preservative", "color", "artificial", "sodium", "phosphate"]):
                analysis["additives"].append(name)
    
    # Extract key nutrients that might be concerning
    if "foodNutrients" in detailed_data:
        concerning_nutrients = ["sodium", "sugar", "saturated fat", "trans fat", "cholesterol"]
        for nutrient in detailed_data["foodNutrients"][:20]:  # Top 20 nutrients
            nutrient_name = nutrient.get("nutrient", {}).get("name", "").lower()
            amount = nutrient.get("amount", 0)
            unit = nutrient.get("nutrient", {}).get("unitName", "")
            
            if any(concern in nutrient_name for concern in concerning_nutrients):
                analysis["nutrients"].append(f"{nutrient_name}: {amount} {unit}")
    
    # Format comprehensive analysis
    usda_analysis = f"""
=== USDA FOODDATA CENTRAL ANALYSIS ===
Food: {analysis['food_name']}
Database ID: {analysis['fdc_id']}

INGREDIENTS LIST:
{chr(10).join(f"• {ing}" for ing in analysis['ingredients'][:15]) if analysis['ingredients'] else "• No detailed ingredients available"}

ADDITIVES & PRESERVATIVES:
{chr(10).join(f"• {add}" for add in analysis['additives']) if analysis['additives'] else "• No specific additives identified"}

KEY NUTRIENTS OF CONCERN:
{chr(10).join(f"• {nut}" for nut in analysis['nutrients']) if analysis['nutrients'] else "• No concerning nutrient levels identified"}

ADDITIONAL USDA DATA AVAILABLE:
• Complete nutrient profile
• Manufacturing details
• Brand information (if applicable)
• Preparation methods
"""
    
    return usda_analysis.strip()

def search_openfoodfacts(food_name: str) -> dict:
    """Search OpenFoodFacts database for food products"""
    try:
        params = {
            "search_terms": food_name,
            "search_simple": 1,
            "action": "process",
            "json": 1,
            "page_size": 5,  # Get top 5 results
            "fields": "product_name,brands,ingredients_text,additives_tags,allergens_tags,nutrition_score_fr,nova_group,ecoscore_grade,code"
        }
        
        response = requests.get(OPENFOODFACTS_SEARCH_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        return data
        
    except Exception as e:
        print(f"OpenFoodFacts search error for '{food_name}': {e}")
        return {"products": [], "error": str(e)}

def get_openfoodfacts_product_details(barcode: str) -> dict:
    """Get detailed product information from OpenFoodFacts using barcode"""
    try:
        url = f"{OPENFOODFACTS_BASE_URL}/product/{barcode}"
        
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        return data
        
    except Exception as e:
        print(f"OpenFoodFacts details error for barcode '{barcode}': {e}")
        return {"error": str(e)}

def analyze_openfoodfacts_data(food_name: str) -> str:
    """Comprehensive analysis of food using OpenFoodFacts database"""
    print(f"Searching OpenFoodFacts database for: {food_name}")
    
    # Search for the food
    search_results = search_openfoodfacts(food_name)
    
    if "error" in search_results or not search_results.get("products"):
        return f"No OpenFoodFacts data found for '{food_name}' - {search_results.get('error', 'No results')}"
    
    products = search_results.get("products", [])
    if not products:
        return f"No OpenFoodFacts products found for '{food_name}'"
    
    # Analyze the best matches (up to 3 products)
    analyses = []
    
    for i, product in enumerate(products[:3]):
        product_name = product.get("product_name", food_name)
        brands = product.get("brands", "No brand")
        barcode = product.get("code", "")
        
        print(f"Analyzing OpenFoodFacts product {i+1}: {product_name}")
        
        # Extract comprehensive information
        analysis = {
            "product_name": product_name,
            "brands": brands,
            "barcode": barcode,
            "ingredients": product.get("ingredients_text", ""),
            "additives": [],
            "allergens": [],
            "nutrition_score": product.get("nutrition_score_fr", "Unknown"),
            "nova_group": product.get("nova_group", "Unknown"),
            "ecoscore": product.get("ecoscore_grade", "Unknown")
        }
        
        # Extract additives (these are particularly important for carcinogen analysis)
        additives_tags = product.get("additives_tags", [])
        if additives_tags:
            analysis["additives"] = [tag.replace("en:", "").replace("-", " ").title() for tag in additives_tags]
        
        # Extract allergens
        allergen_tags = product.get("allergens_tags", [])
        if allergen_tags:
            analysis["allergens"] = [tag.replace("en:", "").replace("-", " ").title() for tag in allergen_tags]
        
        # Format individual product analysis
        product_analysis = f"""
--- OPENFOODFACTS PRODUCT {i+1} ---
Product: {analysis['product_name']}
Brand(s): {analysis['brands']}
Barcode: {analysis['barcode']}

COMPLETE INGREDIENTS LIST:
{analysis['ingredients'] if analysis['ingredients'] else '• No ingredients data available'}

IDENTIFIED ADDITIVES:
{chr(10).join(f"• {additive}" for additive in analysis['additives']) if analysis['additives'] else "• No additives identified"}

ALLERGENS:
{chr(10).join(f"• {allergen}" for allergen in analysis['allergens']) if analysis['allergens'] else "• No allergens identified"}

QUALITY SCORES:
• Nutrition Score: {analysis['nutrition_score']} (A=best, E=worst)
• NOVA Group: {analysis['nova_group']} (1=unprocessed, 4=ultra-processed)
• Eco Score: {analysis['ecoscore']} (A=best environmental impact, E=worst)
"""
        
        analyses.append(product_analysis.strip())
    
    # Combine all product analyses
    final_analysis = f"""
=== OPENFOODFACTS DATABASE ANALYSIS ===
Search Query: {food_name}
Products Found: {len(products)}
Products Analyzed: {len(analyses)}

{chr(10).join(analyses)}

OPENFOODFACTS DATA ADVANTAGES:
• Real consumer product data
• Detailed additive identification
• Processing level classification (NOVA)
• Community-verified ingredients
• Global product coverage
"""
    
    return final_analysis.strip()

def get_combined_food_database_analysis(food_name: str) -> str:
    """Combine data from both USDA and OpenFoodFacts databases"""
    print(f"Performing combined database analysis for: {food_name}")
    
    combined_analysis = f"=== COMBINED DATABASE ANALYSIS FOR: {food_name.upper()} ===\n\n"
    
    # Get USDA data
    usda_data = analyze_usda_food_data(food_name)
    if usda_data and "No USDA data found" not in usda_data:
        combined_analysis += f"{usda_data}\n\n"
    
    # Get OpenFoodFacts data
    off_data = analyze_openfoodfacts_data(food_name)
    if off_data and "No OpenFoodFacts data found" not in off_data:
        combined_analysis += f"{off_data}\n\n"
    
    # Add summary
    combined_analysis += """
=== DATABASE COVERAGE SUMMARY ===
• USDA: Official US government nutrition database
• OpenFoodFacts: Global crowdsourced product database
• Combined: Maximum ingredient and additive identification
• Sources: Government + community verification
"""
    
    return combined_analysis.strip()

def get_ingredient_breakdown(ingredient: str) -> str:
    """Get the chemical makeup and sub-ingredients of a food ingredient using OpenAI"""
    if not openai_client:
        return f"Unable to analyze {ingredient} - OpenAI not configured"
    
    try:
        breakdown_prompt = f"""You are a food science expert. Analyze the ingredient: "{ingredient}"

Provide a comprehensive breakdown including:
1. Primary chemical components and additives
2. Sub-ingredients if it's a processed food
3. Preservatives, colorings, and other chemicals commonly found
4. Any known concerning compounds

Respond in this JSON format:
{{
  "ingredient": "{ingredient}",
  "components": [
    {{"name": "component_name", "type": "chemical/preservative/additive/sub-ingredient", "description": "brief description"}},
    ...
  ],
  "processing_chemicals": ["chemical1", "chemical2", ...],
  "potential_concerns": ["concern1", "concern2", ...]
}}

Focus on components that might have health implications. Be thorough but factual."""

        chat = openai_client.chat.completions.create(
            model=OPENAI_MODEL,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "You are a food science expert specializing in ingredient analysis."},
                {"role": "user", "content": breakdown_prompt}
            ],
            temperature=0.2,
        )
        
        return chat.choices[0].message.content or ""
        
    except Exception as e:
        print(f"Error getting ingredient breakdown for {ingredient}: {e}")
        return f"Error analyzing {ingredient}: {str(e)}"

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
            entry = {"name": ing, "risk_level": "unknown", "score": "unknown", "source": "unknown", "explanation": "unknown", "nova_group": None}
            result.append(entry)
            continue
        llm_item = llm_dict.get(key, {})
        known = KNOWN_CARCINOGEN_SCORES.get(key, {})
        # If LLM and known are both empty, mark as unknown
        if not llm_item and not known:
            entry = {"name": ing, "risk_level": "unknown", "score": "unknown", "source": "unknown", "explanation": "unknown", "nova_group": None}
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
            "nova_group": llm_item.get("nova_group") or known.get("nova_group", None),
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

def validate_food_input(ingredients: str) -> Dict[str, Any]:
    """
    Validate if the input contains food products using OpenAI and database searches.
    Returns validation result with any non-food items identified.
    """
    if not openai_client:
        return {"is_valid": True, "non_food_items": [], "message": "OpenAI not configured, skipping validation"}
    
    ingredient_list = [i.strip() for i in ingredients.split(",") if i.strip()]
    if not ingredient_list:
        return {"is_valid": False, "non_food_items": [], "message": "No ingredients provided"}
    
    # Create a comprehensive validation prompt
    validation_prompt = f"""
You are a food safety expert. Your task is to determine if each item in the following list is a food product that could be consumed by humans.

Items to validate: {', '.join(ingredient_list)}

For each item, determine:
1. Is it a food product, ingredient, or consumable item?
2. Is it commonly found in food products or used in cooking/eating?

Consider these as FOOD ITEMS:
- Raw ingredients (meat, vegetables, fruits, grains, etc.)
- Processed foods (bread, cheese, canned goods, etc.)
- Beverages (juice, soda, water, etc.)
- Condiments and seasonings (salt, pepper, ketchup, etc.)
- Food additives and preservatives
- Cooking ingredients (oil, flour, sugar, etc.)
- Natural food products (honey, nuts, seeds, etc.)

Consider these as NON-FOOD ITEMS:
- Household products (soap, detergent, cleaning supplies)
- Personal care items (shampoo, toothpaste, cosmetics)
- Medications and supplements (unless specifically food-based)
- Industrial chemicals not used in food
- Non-consumable materials (plastic, metal, etc.)
- Plants that are not edible
- Animals that are not typically consumed as food

Respond with a JSON object in this exact format:
{{
    "validation_results": [
        {{
            "item": "item_name",
            "is_food": true/false,
            "confidence": 0.0-1.0,
            "reasoning": "brief explanation"
        }}
    ],
    "overall_valid": true/false,
    "non_food_items": ["list", "of", "non-food", "items"],
    "message": "overall validation message"
}}

Be strict in your validation - if you're unsure whether something is food, mark it as non-food.
"""

    try:
        response = openai_client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": validation_prompt}],
            temperature=0.1,
            response_format={"type": "json_object"}
        )
        
        validation_result = json.loads(response.choices[0].message.content)
        
        # Also do a quick database search to cross-validate
        database_validation = validate_with_databases(ingredient_list)
        
        # Combine results - prioritize AI validation, only use database validation as additional confirmation
        ai_non_food = set(validation_result.get("non_food_items", []))
        db_non_food = set(database_validation.get("non_food_items", []))
        
        # Only flag as non-food if BOTH AI and database agree it's non-food, OR if AI is very confident it's non-food
        final_non_food = set()
        for item in ai_non_food:
            # Check if AI validation shows high confidence it's non-food
            ai_details = validation_result.get("validation_details", [])
            ai_item_detail = next((d for d in ai_details if d.get("item") == item), {})
            ai_confidence = ai_item_detail.get("confidence", 0.0)
            
            # If AI is very confident it's non-food (confidence > 0.8), or if both AI and DB agree
            if ai_confidence > 0.8 or item in db_non_food:
                final_non_food.add(item)
        
        return {
            "is_valid": len(final_non_food) == 0,
            "non_food_items": list(final_non_food),
            "message": validation_result.get("message", ""),
            "validation_details": validation_result.get("validation_results", []),
            "database_validation": database_validation
        }
        
    except Exception as e:
        print(f"Food validation error: {e}")
        return {"is_valid": True, "non_food_items": [], "message": f"Validation error: {str(e)}"}

def validate_with_databases(ingredient_list: List[str]) -> Dict[str, Any]:
    """
    Cross-validate ingredients using USDA and OpenFoodFacts databases.
    """
    non_food_items = []
    validation_details = []
    
    for ingredient in ingredient_list:
        is_food = False
        confidence = 0.0
        
        # Check USDA database
        try:
            usda_results = search_usda_foods(ingredient, limit=3)
            if usda_results and len(usda_results) > 0:
                is_food = True
                confidence += 0.5
        except:
            pass
        
        # Check OpenFoodFacts database
        try:
            off_results = search_openfoodfacts(ingredient, limit=3)
            if off_results and len(off_results) > 0:
                is_food = True
                confidence += 0.5
        except:
            pass
        
        if not is_food:
            non_food_items.append(ingredient)
        
        validation_details.append({
            "item": ingredient,
            "is_food": is_food,
            "confidence": confidence,
            "usda_found": len(search_usda_foods(ingredient, limit=1)) > 0 if 'usda_results' in locals() else False,
            "off_found": len(search_openfoodfacts(ingredient, limit=1)) > 0 if 'off_results' in locals() else False
        })
    
    return {
        "non_food_items": non_food_items,
        "validation_details": validation_details,
        "message": f"Database validation found {len(non_food_items)} non-food items" if non_food_items else "All items found in food databases"
    }

def analyze_ingredients(ingredients: str):
    # First, validate that all inputs are food products
    validation_result = validate_food_input(ingredients)
    if not validation_result["is_valid"]:
        return {
            "error": f"Non-food items detected: {', '.join(validation_result['non_food_items'])}. Please enter only food products, ingredients, or consumable items.",
            "validation_details": validation_result
        }
    
    print(f"Validation passed for: {ingredients}")
    
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
            
        # Step 1: Get comprehensive database information (USDA + OpenFoodFacts)
        print(f"Querying food databases for: {ingredient}")
        database_data = get_combined_food_database_analysis(ingredient)
        
        # Step 2: Get ingredient breakdown (components, chemicals, sub-ingredients)
        print(f"Analyzing component breakdown for: {ingredient}")
        breakdown_json = get_ingredient_breakdown(ingredient)
        
        # Step 2: Extract components for individual risk assessment
        components_to_analyze = []
        breakdown_info = ""
        
        try:
            breakdown_data = json.loads(breakdown_json)
            breakdown_info = f"Ingredient breakdown: {breakdown_json}"
            
            # Collect all components for analysis
            if "components" in breakdown_data:
                for comp in breakdown_data["components"]:
                    components_to_analyze.append(comp["name"])
            
            if "processing_chemicals" in breakdown_data:
                components_to_analyze.extend(breakdown_data["processing_chemicals"])
                
            if "potential_concerns" in breakdown_data:
                components_to_analyze.extend(breakdown_data["potential_concerns"])
                
        except json.JSONDecodeError:
            print(f"Could not parse breakdown JSON for {ingredient}")
            breakdown_info = f"Component analysis: {breakdown_json}"
            components_to_analyze = [ingredient]  # Fallback to original ingredient
        
        # Step 3: Perform comprehensive multi-angle research on key components
        component_research = []
        priority_components = components_to_analyze[:5]  # Focus on top 5 most important components
        
        print(f"Performing detailed research on {len(priority_components)} key components")
        
        for component in priority_components:
            if USE_WEB_SEARCH and SERPAPI_KEY != "your_serpapi_key_here":
                print(f"Deep research analysis for: {component}")
                detailed_research = perform_multi_angle_search(component)
                component_research.append(f"=== COMPREHENSIVE ANALYSIS: {component.upper()} ===\n{detailed_research}")
                
                # Add a small delay to respect API rate limits
                time.sleep(0.5)
        
        # Step 4: Retrieve general context for the main ingredient
        general_context = retrieve_context(ingredient)
        
        # Step 5: Perform additional targeted search for the main ingredient
        main_ingredient_research = ""
        if USE_WEB_SEARCH and SERPAPI_KEY != "your_serpapi_key_here":
            print(f"Researching main ingredient: {ingredient}")
            main_ingredient_research = perform_multi_angle_search(ingredient)
        
        # Step 6: Compile all research including database data
        all_research = ""
        
        # Add combined database data first (most authoritative)
        if database_data and any(keyword not in database_data for keyword in ["No USDA data found", "No OpenFoodFacts data found"]):
            all_research += f"{database_data}\n\n"
        
        if main_ingredient_research:
            all_research += f"=== MAIN INGREDIENT RESEARCH: {ingredient.upper()} ===\n{main_ingredient_research}\n\n"
        
        if component_research:
            all_research += "\n\n".join(component_research)
        
        if not all_research:
            all_research = "No detailed research available - using static knowledge base only"
        
        prompt = f"""<s>[INST] You are an expert in food safety and carcinogen risk assessment.

INGREDIENT TO ANALYZE: {ingredient}

COMPONENT BREAKDOWN:
{breakdown_info}

RESEARCH ON INDIVIDUAL COMPONENTS:
{all_research}

GENERAL CONTEXT:
{general_context}

Based on ALL the above information, provide a comprehensive carcinogen risk assessment for "{ingredient}". Consider:
1. Direct risks from the main ingredient
2. Risks from chemical components, preservatives, and additives
3. Processing-related risks
4. Cumulative risk from all components

You must respond with ONLY a valid JSON object in this exact format, no other text:
{{
  "name": "{ingredient}",
  "risk_level": "Low/Medium/High/Unknown",
  "score": 0-100,
  "source": "Primary sources cited or 'Multiple sources'",
  "explanation": "Comprehensive explanation covering the ingredient and its components, highlighting main risk factors",
  "nova_group": "1-4 or null (extract from OpenFoodFacts data if available)"
}}

Scoring guidelines:
- 0-30: Low risk (minimal or no carcinogenic evidence)
- 31-60: Medium risk (some concerning evidence or components)
- 61-100: High risk (strong evidence or multiple concerning components)

NOVA Group extraction (CRITICAL - look for this exact pattern):
- Search the provided data for text like "NOVA Group: 1", "NOVA Group: 2", "NOVA Group: 3", or "NOVA Group: 4"
- Extract the number after "NOVA Group:" and use it as the nova_group value
- If you find "NOVA Group: 4", set nova_group to "4"
- If you find "NOVA Group: 3", set nova_group to "3"
- If you find "NOVA Group: 2", set nova_group to "2"
- If you find "NOVA Group: 1", set nova_group to "1"
- If you find "NOVA Group: Unknown" or no NOVA Group information, set nova_group to null
- IMPORTANT: Always include the nova_group field in your JSON response, even if null

IMPORTANT: Respond ONLY with the JSON object, no additional text, no explanations outside the JSON. [/INST]"""
        
        try:
            # Generate response using OpenAI Chat Completions in JSON mode
            if not openai_client:
                raise RuntimeError("OPENAI_API_KEY is not configured")

            chat = openai_client.chat.completions.create(
                model=OPENAI_MODEL,
                response_format={"type": "json_object"},
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an expert in food safety and carcinogen risk assessment. "
                            "Always output only valid JSON with the required keys."
                        ),
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
                temperature=0.2,
            )

            llm_output = (chat.choices[0].message.content or "").strip()
            
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
                            "explanation": f"Unable to parse AI response. Raw response: {llm_output[:200]}...",
                            "nova_group": None
                        })
                else:
                    # No JSON found in response
                    results.append({
                        "name": ingredient,
                        "risk_level": "unknown",
                        "score": "unknown", 
                        "source": "N/A",
                        "explanation": f"AI did not return valid JSON. Raw response: {llm_output[:200]}...",
                        "nova_group": None
                    })
        
        except Exception as e:
            results.append({
                "name": ingredient,
                "risk_level": "unknown",
                "score": "unknown",
                "source": "N/A", 
                "explanation": f"Error during analysis: {str(e)}",
                "nova_group": None
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

@app.post("/ingredients")
def get_llm_response(
    request: Union[IngredientRequest, list[ProductRequest]] = Body(...)
):
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
        "provider": "openai",
        "model": OPENAI_MODEL,
        "openai_configured": bool(openai_client is not None),
    }

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "provider": "openai",
        "model": OPENAI_MODEL,
        "openai_configured": bool(openai_client is not None),
    } 