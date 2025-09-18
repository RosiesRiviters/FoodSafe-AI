#!/usr/bin/env python3
import sys
import os
sys.path.append('py')

# Import the OpenAI client and model from rag_server
from rag_server import openai_client, OPENAI_MODEL, get_combined_food_database_analysis

def debug_ai_prompt():
    """Debug what exactly the AI is receiving and returning"""
    print("DEBUG: AI Prompt and Response")
    print("="*60)
    
    # Get the database data for a known product with NOVA group
    print("1. Getting database data for 'oreo'...")
    database_data = get_combined_food_database_analysis('oreo')
    
    # Show the NOVA group data that should be present
    print("\n2. NOVA Groups found in database data:")
    lines = database_data.split('\n')
    nova_lines = [line for line in lines if 'NOVA Group:' in line]
    for line in nova_lines:
        print(f"   {line.strip()}")
    
    # Create the exact prompt that would be sent to the AI
    ingredient = "oreo"
    prompt = f"""Based on the comprehensive research data below, analyze the carcinogen risk for the ingredient: {ingredient}

COMPONENT BREAKDOWN:
The ingredient has been analyzed for its chemical makeup, sub-ingredients, and additives.

RESEARCH ON INDIVIDUAL COMPONENTS:
Comprehensive multi-angle research has been conducted on the ingredient's components.

COMPREHENSIVE RESEARCH DATA:
{database_data}

Based on this comprehensive analysis, evaluate the carcinogen risk considering:
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

IMPORTANT: Respond ONLY with the JSON object, no additional text, no explanations outside the JSON."""
    
    print(f"\n3. Prompt length: {len(prompt)} characters")
    print(f"\n4. Sample of prompt (first 500 chars):")
    print(prompt[:500] + "...")
    
    print("\n5. Calling OpenAI API directly...")
    try:
        if not openai_client:
            print("✗ OpenAI client not configured")
            return
            
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
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
        )
        
        ai_response = chat.choices[0].message.content or ""
        print(f"\n6. AI Response:")
        print(ai_response)
        
        # Try to parse the response
        import json
        try:
            result = json.loads(ai_response)
            print(f"\n7. Parsed JSON:")
            for key, value in result.items():
                print(f"   {key}: {repr(value)}")
                
            nova_group = result.get('nova_group')
            if nova_group:
                print(f"\n✓ NOVA Group successfully extracted: {nova_group}")
            else:
                print(f"\n✗ NOVA Group not extracted (value: {repr(nova_group)})")
                print("   Check if AI is following instructions correctly")
                
        except json.JSONDecodeError as e:
            print(f"\n✗ JSON parsing failed: {e}")
            
    except Exception as e:
        print(f"✗ API call failed: {e}")

if __name__ == "__main__":
    debug_ai_prompt()

