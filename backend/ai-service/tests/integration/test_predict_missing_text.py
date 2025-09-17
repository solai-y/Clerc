# tests/integration/test_predict_missing_text.py
def test_predict_missing_text(client):
    resp = client.post("/predict", json={})
    assert resp.status_code == 400
    data = resp.get_json()
    assert "Missing required field 'text'." in data["error"]
