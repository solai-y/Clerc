# tests/integration/test_predict_missing_text.py
def test_predict_missing_text(client):
    resp = client.post("/predict", json={})
    assert resp.status_code == 422  # FastAPI validation error for missing required field
    data = resp.json()
    assert "detail" in data
