#!/usr/bin/env python3
import requests
import json

def test_single_ingredient():
    """Test a single ingredient to see the full response"""
    print("Testing single ingredient: oreo")
    print("="*50)
    
    try:
        # Call the API
        data = {'ingredients': 'oreo'}
        response = requests.post('http://127.0.0.1:8002/ingredients', json=data, timeout=60)
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Full response:")
            print(json.dumps(result, indent=2))
            
            # Look specifically at NOVA group
            ingredients = result.get('ingredients', [])
            for item in ingredients:
                nova_group = item.get('nova_group')
                print(f"\nNOVA Group field: {repr(nova_group)}")
                print(f"Type: {type(nova_group)}")
                
                # Check if it's in the explanation
                explanation = item.get('explanation', '')
                if 'nova' in explanation.lower() or 'group' in explanation.lower():
                    print(f"NOVA mentioned in explanation: {explanation[:200]}...")
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_single_ingredient()

