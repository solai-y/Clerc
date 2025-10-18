# tests/integration/test_predict_success.py
def test_predict_success(client, app_module):
    raw_text = "This Q2 earnings report shows us that there is a need for us to buy more stock of Company X!!!"
    resp = client.post("/predict", json={"text": raw_text})
    assert resp.status_code == 200, resp.text
    data = resp.json()

    # response shape
    assert "prediction" in data and "elapsed_seconds" in data and "processed_text" in data

    # check preprocessing matches server's clean_text
    expected = app_module.clean_text(raw_text)
    assert data["processed_text"] == expected

    # basic structure of prediction
    p = data["prediction"]
    assert "primary" in p and "secondary" in p and "tertiary" in p
    assert p["primary"]["pred"] == "Disclosure"
    assert "confidence" in p["primary"]
