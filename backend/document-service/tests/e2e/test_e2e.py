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

    # Check new API response structure
    try:
        assert data.get("status") == "success"
        print("[PASS] Status is 'success'.")
    except AssertionError:
        print(f"[FAIL] Expected status 'success', got '{data.get('status')}'")
        raise

    try:
        assert data.get("message") == "Document service is reachable"
        print("[PASS] Message key matches expected value.")
    except AssertionError:
        print(f"[FAIL] Expected message 'Document service is reachable', got '{data.get('message')}'")
        raise

    try:
        assert "data" in data
        assert data["data"]["service"] == "document-service"
        print("[PASS] Data structure is correct.")
    except (AssertionError, KeyError) as e:
        print(f"[FAIL] Data structure check failed: {e}")
        raise

    try:
        assert "timestamp" in data
        print("[PASS] Timestamp is present.")
    except AssertionError:
        print("[FAIL] Timestamp is missing")
        raise

    print("[SUCCESS] E2E test for GET /e2e endpoint completed successfully.")

def test_health_endpoint():
    print("\n[TEST] Running E2E test for GET /health endpoint...")

    url = "http://localhost:5003/health"
    print(f"[INFO] Sending GET request to {url}")

    try:
        response = requests.get(url)
        print(f"[DEBUG] Received response with status code: {response.status_code}")
    except Exception as e:
        print(f"[FAIL] Exception occurred while sending request: {e}")
        raise

    try:
        data = response.json()
        print(f"[DEBUG] Response JSON data: {data}")
    except Exception as e:
        print(f"[FAIL] Failed to parse JSON: {e}")
        raise

    # Health endpoint can return 200 (healthy) or 503 (unhealthy)
    try:
        assert response.status_code in [200, 503]
        print(f"[PASS] Status code is {response.status_code} (expected 200 or 503).")
    except AssertionError:
        print(f"[FAIL] Expected status code 200 or 503, got {response.status_code}")
        raise

    try:
        assert "status" in data
        assert "data" in data
        assert "timestamp" in data
        print("[PASS] Response structure is correct.")
    except (AssertionError, KeyError) as e:
        print(f"[FAIL] Response structure check failed: {e}")
        raise

    print("[SUCCESS] E2E test for GET /health endpoint completed successfully.")

if __name__ == "__main__":
    test_e2e_endpoint()
    test_health_endpoint()