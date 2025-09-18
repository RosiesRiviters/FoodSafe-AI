#!/usr/bin/env python3
import requests
import json

def test_uncached_ingredient():
    """Test with a new ingredient to avoid cache"""
    ingredients = ['corn flakes cereal', 'pepsi cola', 'mcdonalds burger']
    
    for ingredient in ingredients:
        print(f"\nTesting: {ingredient}")
        print("="*40)
        
        try:
            data = {'ingredients': ingredient}
            response = requests.post('http://127.0.0.1:8002/ingredients', json=data, timeout=60)
            
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                cached = result.get('cached', False)
                print(f"Cached: {cached}")
                
                ingredients_list = result.get('ingredients', [])
                for item in ingredients_list:
                    name = item.get('name', 'N/A')
                    nova_group = item.get('nova_group')
                    risk_level = item.get('risk_level', 'N/A')
                    score = item.get('score', 'N/A')
                    
                    print(f"  Name: {name}")
                    print(f"  Risk Level: {risk_level}")
                    print(f"  Score: {score}")
                    print(f"  NOVA Group: {nova_group} (type: {type(nova_group)})")
                    
                    if nova_group:
                        print(f"  ✓ NOVA Group extracted: {nova_group}")
                    else:
                        print(f"  ✗ NOVA Group missing or null")
                    
                    # Check if NOVA is mentioned in explanation
                    explanation = item.get('explanation', '')
                    if 'nova' in explanation.lower():
                        print(f"  ⚠ NOVA mentioned in explanation but not extracted")
                        
            else:
                print(f"Error: {response.text}")
                
        except Exception as e:
            print(f"Exception: {e}")

if __name__ == "__main__":
    test_uncached_ingredient()

