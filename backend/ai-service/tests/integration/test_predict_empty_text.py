# tests/integration/test_predict_empty_text.py
def test_predict_empty_text(client):
    resp = client.post("/predict", json={"text": "   "})
    assert resp.status_code == 400
    data = resp.get_json()
    assert "'text' must be a non-empty string." in data["error"]
