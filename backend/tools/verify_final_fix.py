import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def get_token():
    # Assuming standard login for testing
    resp = requests.post(f"{BASE_URL}/login", data={"username": "safina", "password": "safinapassword"})
    return resp.json().get("access_token")

def test_filters():
    token = get_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    print("--- Testing 'all' filters ---")
    # Test project="all"
    resp = requests.get(f"{BASE_URL}/expenses?project=all&limit=10", headers=headers)
    data = resp.json()
    print(f"Total with project='all': {data['total']}")
    
    # Test user_id="all"
    resp = requests.get(f"{BASE_URL}/expenses?user_id=all&limit=10", headers=headers)
    data = resp.json()
    print(f"Total with user_id='all': {data['total']}")

    print("\n--- Testing Export Columns ---")
    # Check export-xlsx response (we can't easily parse XLSX but we can check if it returns 200)
    resp = requests.get(f"{BASE_URL}/expenses/export-xlsx?project=all", headers=headers)
    if resp.status_code == 200:
        print("Export XLSX successful (Status 200)")
    else:
        print(f"Export XLSX failed: {resp.status_code}")

if __name__ == "__main__":
    try:
        test_filters()
    except Exception as e:
        print(f"Error during verification: {e}")
