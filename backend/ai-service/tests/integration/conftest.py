# tests/integration/conftest.py
import sys
import types
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

HERE = Path(__file__).resolve().parent
SERVICE_ROOT = HERE.parent.parent  # .../ai-service

# ---------------- Dummy model used by tests ----------------
class DummyHierModel:
    """Mimics your wrapper's interface: .predict(List[str]) -> List[Dict]."""
    def __init__(self, version="v1"):
        self.version = version

    def predict(self, texts):
        out = []
        for _t in texts:
            out.append({
                "primary":   {"pred": "Disclosure", "confidence": 0.91,
                              "key_evidence": {"supporting": [], "opposing": []}},
                "secondary": {"pred": "SEC_Filings", "confidence": 0.83, "primary": "Disclosure",
                              "key_evidence": {"supporting": [], "opposing": []}},
                "tertiary":  {"pred": "10-K", "confidence": 0.77, "primary": "Disclosure", "secondary": "SEC_Filings",
                              "key_evidence": {"supporting": [], "opposing": []}},
                "model_version": self.version,
            })
        return out

@pytest.fixture(scope="session", autouse=True)
def _prepare_models_dir():
    """
    Create marker files so app.py's ensure_models_ready() won't try to auto-train.
    We don't need valid joblibs because we inject a fake train module.
    """
    models_dir = SERVICE_ROOT / "models_hier"
    models_dir.mkdir(exist_ok=True)
    (models_dir / "primary.joblib").write_bytes(b"dummy")
    (models_dir / "best_model.joblib").write_bytes(b"dummy")
    yield
    # (Optional) clean-up can go here.

@pytest.fixture(scope="session")
def app_module(_prepare_models_dir):
    """
    Inject a fake `train` module before importing app.py so
    `from train import build_best_model` resolves to our stub.
    """
    fake_train = types.ModuleType("train")

    def build_best_model(models_dir: Path):
        # Return a predictable dummy model
        return DummyHierModel(version="v1")

    fake_train.build_best_model = build_best_model
    sys.modules["train"] = fake_train

    sys.path.insert(0, str(SERVICE_ROOT))
    import importlib
    app_mod = importlib.import_module("app")  # imports ai-service/app.py
    return app_mod

@pytest.fixture
def client(app_module):
    # FastAPI TestClient
    return TestClient(app_module.app)
