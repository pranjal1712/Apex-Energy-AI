import os
import sys

# Mocking environment variables
os.environ["GROQ_API_KEY"] = "key1,key2,key3"
os.environ["GROQ_API_KEYS"] = "key4,key5,key6,key7"

# Path to the rotator.py
sys.path.append(os.path.dirname(__file__))

from rotator import APIKeyRotator

def test_rotator():
    rotator = APIKeyRotator("GROQ_API_KEY")
    keys = rotator.get_all_keys()
    print(f"Detected Keys: {keys}")
    print(f"Count: {len(keys)}")
    
    if len(keys) == 7:
        print("SUCCESS: 7 unique keys detected.")
    else:
        print(f"FAILURE: Expected 7 keys, got {len(keys)}")

if __name__ == "__main__":
    test_rotator()
