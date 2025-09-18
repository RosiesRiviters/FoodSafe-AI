#!/usr/bin/env python3
import requests
import json
import uuid

def test_fresh_nova():
    """Test NOVA group with a completely fresh ingredient"""
    # Use a unique ingredient name to ensure no caching
    unique_ingredient = f"oreo cookies test {uuid.uuid4().hex[:8]}"
    
    print(f"Testing fresh ingredient: {unique_ingredient}")
    print("="*60)
    
    try:
        data = {'ingredients': unique_ingredient}
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
                explanation = item.get('explanation', '')
                
                print(f"\n--- RESULTS ---")
                print(f"Name: {name}")
                print(f"Risk Level: {risk_level}")
                print(f"Score: {score}")
                print(f"NOVA Group: {repr(nova_group)} (type: {type(nova_group)})")
                print(f"Explanation snippet: {explanation[:100]}...")
                
                if nova_group:
                    print(f"✓ SUCCESS: NOVA Group extracted: {nova_group}")
                else:
                    print(f"✗ FAILED: NOVA Group missing")
                    
                # Check if NOVA is mentioned in explanation
                if 'nova' in explanation.lower():
                    print(f"⚠ NOVA mentioned in explanation")
                    nova_mentions = [line.strip() for line in explanation.split('.') if 'nova' in line.lower()]
                    for mention in nova_mentions:
                        print(f"   -> {mention}")
                        
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_fresh_nova()

