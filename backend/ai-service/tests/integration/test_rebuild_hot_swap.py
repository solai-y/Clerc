# tests/integration/test_rebuild_hot_swap.py
import time
import conftest  # <- gives access to DummyHierModel defined in conftest

def test_rebuild_hot_swap(client, app_module, monkeypatch):
    # Sanity: /predict uses v1 now
    r0 = client.post("/predict", json={"text": "hello world"})
    assert r0.status_code == 200
    v0 = r0.json()["prediction"]["model_version"]
    assert v0 == "v1"

    # Simulate slow training
    def fake_run(cmd, check):
        time.sleep(0.25)
        return 0
    monkeypatch.setattr(app_module.subprocess, "run", fake_run, raising=True)

    # After rebuild, loader returns v2
    def fake_build_best_model(_models_dir):
        return conftest.DummyHierModel(version="v2")
    monkeypatch.setattr(app_module, "build_best_model", fake_build_best_model, raising=True)

    # Kick off rebuild
    r1 = client.post("/rebuild")
    assert r1.status_code == 202

    # During rebuild -> still v1
    r2 = client.post("/predict", json={"text": "hello again"})
    assert r2.status_code == 200
    assert r2.json()["prediction"]["model_version"] == "v1"

    # After rebuild -> v2
    time.sleep(0.35)
    r3 = client.post("/predict", json={"text": "final check"})
    assert r3.status_code == 200
    assert r3.json()["prediction"]["model_version"] == "v2"
