#!/usr/bin/env python3
import requests
import json

def test_nova_group():
    """Test NOVA group integration"""
    print("Testing NOVA Group integration...")
    print("="*60)
    
    # Test with foods that should have OpenFoodFacts data
    test_foods = ['oreo cookies', 'corn flakes', 'coca cola']
    
    for food in test_foods:
        print(f"\nTesting: {food}")
        print("-" * 40)
        
        try:
            data = {'ingredients': food}
            response = requests.post(
                'http://127.0.0.1:8002/ingredients', 
                json=data, 
                timeout=60
            )
            
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                ingredients = result.get('ingredients', [])
                
                for item in ingredients:
                    print(f"  Name: {item.get('name', 'N/A')}")
                    print(f"  Risk Level: {item.get('risk_level', 'N/A')}")
                    print(f"  Score: {item.get('score', 'N/A')}")
                    print(f"  NOVA Group: {item.get('nova_group', 'N/A')}")
                    print(f"  Source: {item.get('source', 'N/A')}")
                    print()
                    
                # Check if NOVA group was extracted
                nova_groups = [item.get('nova_group') for item in ingredients if item.get('nova_group')]
                if nova_groups:
                    print(f"✓ NOVA groups found: {nova_groups}")
                else:
                    print("⚠ No NOVA groups extracted")
            else:
                print(f"✗ Error: {response.status_code}")
                print(f"Response: {response.text[:200]}")
                
        except Exception as e:
            print(f"✗ Exception: {e}")
    
    print("\n" + "="*60)
    print("NOVA Group Test Complete")

if __name__ == "__main__":
    test_nova_group()
