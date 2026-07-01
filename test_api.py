import requests
import json
import time

def test_generate(mode, target_entity, venue):
    print(f"\n--- Testing Mode: {mode.upper()} ---")
    print(f"Target: {target_entity} | Venue: {venue}")
    
    start = time.time()
    try:
        response = requests.post(
            'http://localhost:8000/generate', 
            json={'mode': mode, 'target_entity': target_entity, 'venue': venue}
        )
        response.raise_for_status()
        data = response.json()
        print(f"Time Taken: {round(time.time() - start, 2)} seconds")
        print("\nPlaybook Output:\n")
        print(data['playbook'])
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # Test Batting Mode
    test_generate("batting", "Australia", "M. Chinnaswamy Stadium")
    
    # Test Bowling Mode
    test_generate("bowling", "Travis Head", "Wankhede Stadium")
