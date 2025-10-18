# tests/integration/test_predict_invalid_json_formdata.py
def test_predict_invalid_json_formdata(client):
    # Send form-data instead of JSON; FastAPI should return 422 validation error
    resp = client.post("/predict", data={"text": "hello"})
    assert resp.status_code == 422  # FastAPI validation error
    data = resp.json()
    assert "detail" in data
