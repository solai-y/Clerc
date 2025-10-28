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

    # basic structure of prediction (now arrays for multi-label support)
    p = data["prediction"]
    assert "primary" in p and "secondary" in p and "tertiary" in p

    # Verify arrays are returned
    assert isinstance(p["primary"], list), "primary should be a list"
    assert isinstance(p["secondary"], list), "secondary should be a list"
    assert isinstance(p["tertiary"], list), "tertiary should be a list"

    # Verify at least one prediction per level
    assert len(p["primary"]) > 0, "primary should have at least one prediction"
    assert len(p["secondary"]) > 0, "secondary should have at least one prediction"
    assert len(p["tertiary"]) > 0, "tertiary should have at least one prediction"

    # Verify structure of first prediction
    assert "label" in p["primary"][0], "primary prediction should have 'label'"
    assert "confidence" in p["primary"][0], "primary prediction should have 'confidence'"
    assert p["primary"][0]["label"] == "Disclosure", f"Expected 'Disclosure', got {p['primary'][0]['label']}"
