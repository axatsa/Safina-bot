import requests
import json

base_url = "http://localhost:8000/api"
token = "YOUR_TOKEN_HERE" # Need a valid token to test

def test_generate_blank():
    url = f"{base_url}/blanks/generate"
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "template": "land",
        "purpose": "Test API Blank",
        "items": [
            {"name": "Test Item", "qty": 2, "amount": 50000, "currency": "UZS"}
        ]
    }
    
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        with open("tmp/test_blank.docx", "wb") as f:
            f.write(response.content)
        print("Success! File saved to tmp/test_blank.docx")
    else:
        print(f"Error {response.status_code}: {response.text}")

if __name__ == "__main__":
    # This script requires a running server and valid token
    # For now, it's a template for manual verification
    print("Test script ready. Requires manual execution with valid token.")
