#!/usr/bin/env python3
import sys
sys.path.append('py')
from rag_server import get_combined_food_database_analysis, get_llm_response

def debug_nova_extraction():
    """Debug NOVA group extraction"""
    print("DEBUG: NOVA Group Extraction")
    print("="*60)
    
    # Get the database data
    print("1. Getting database data for 'oreo'...")
    database_data = get_combined_food_database_analysis('oreo')
    
    # Check for NOVA Group in data
    print("\n2. Checking for NOVA Group in database data:")
    lines = database_data.split('\n')
    nova_lines = [line for line in lines if 'NOVA Group:' in line]
    for line in nova_lines:
        print(f"   Found: {line.strip()}")
    
    # Create a simple test prompt
    print("\n3. Testing AI extraction with sample data...")
    test_prompt = f"""
Based on the following food data, analyze the carcinogen risk for "oreo":

{database_data[:1000]}...

You must respond with ONLY a valid JSON object in this exact format, no other text:
{{
  "name": "oreo",
  "risk_level": "Low/Medium/High/Unknown",
  "score": 0-100,
  "source": "Primary sources cited or 'Multiple sources'",
  "explanation": "Comprehensive explanation covering the ingredient and its components, highlighting main risk factors",
  "nova_group": "1-4 or null (extract from OpenFoodFacts data if available)"
}}

NOVA Group extraction (CRITICAL - look for this exact pattern):
- Search the provided data for text like "NOVA Group: 1", "NOVA Group: 2", "NOVA Group: 3", or "NOVA Group: 4"
- Extract the number after "NOVA Group:" and use it as the nova_group value
- If you find "NOVA Group: 4", set nova_group to "4"
- IMPORTANT: Always include the nova_group field in your JSON response, even if null
"""
    
    print("\n4. Calling AI with test prompt...")
    try:
        response = get_llm_response(test_prompt)
        print(f"AI Response: {response}")
        
        # Try to parse the response
        import json
        try:
            result = json.loads(response)
            print(f"\n5. Parsed JSON:")
            for key, value in result.items():
                print(f"   {key}: {value}")
                
            nova_group = result.get('nova_group')
            if nova_group:
                print(f"\n✓ NOVA Group successfully extracted: {nova_group}")
            else:
                print(f"\n✗ NOVA Group not extracted (value: {nova_group})")
                
        except json.JSONDecodeError as e:
            print(f"\n✗ JSON parsing failed: {e}")
            
    except Exception as e:
        print(f"✗ AI call failed: {e}")

if __name__ == "__main__":
    debug_nova_extraction()

