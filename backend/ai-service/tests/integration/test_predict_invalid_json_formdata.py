# tests/integration/test_predict_invalid_json_formdata.py
def test_predict_invalid_json_formdata(client):
    # Send form-data instead of JSON; app should return 400 "Invalid JSON."
    resp = client.post("/predict", data={"text": "hello"})
    assert resp.status_code == 400
    data = resp.get_json()
    assert data["error"].lower().startswith("invalid json")
