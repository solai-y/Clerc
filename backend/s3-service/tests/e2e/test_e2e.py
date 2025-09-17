import requests

def test_e2e_endpoint():
    print("\n[TEST] Running E2E test for GET /e2e endpoint...")

    url = "http://localhost:5003/e2e"
    print(f"[INFO] Sending GET request to {url}")

    try:
        response = requests.get(url)
        print(f"[DEBUG] Received response with status code: {response.status_code}")
    except Exception as e:
        print(f"[FAIL] Exception occurred while sending request: {e}")
        raise

    try:
        assert response.status_code == 200
        print("[PASS] Status code is 200 (OK).")
    except AssertionError:
        print(f"[FAIL] Expected status code 200, got {response.status_code}")
        raise

    try:
        data = response.json()
        print(f"[DEBUG] Response JSON data: {data}")
    except Exception as e:
        print(f"[FAIL] Failed to parse JSON: {e}")
        raise

    try:
        assert data.get("message") == "S3 service is reachable"
        print("[PASS] Message key matches expected value.")
    except AssertionError:
        print(f"[FAIL] Expected message 'S3 service is reachable', got '{data.get('message')}'")
        raise

    print("[SUCCESS] E2E test for GET /e2e endpoint completed successfully.")

if __name__ == "__main__":
    test_e2e_endpoint()