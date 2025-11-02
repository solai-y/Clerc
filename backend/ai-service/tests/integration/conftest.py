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
    """Mimics your wrapper's interface: .predict(List[str]) -> List[Dict].
    Returns multiclass format with arrays of predictions per level."""
    def __init__(self, version="v1"):
        self.version = version

    def predict(self, texts):
        out = []
        for _t in texts:
            # Return multiclass format: each level has an array of predictions
            out.append({
                "primary": [
                    {"label": "Disclosure", "confidence": 0.91,
                     "key_evidence": {"supporting": [], "opposing": []}}
                ],
                "secondary": [
                    {"label": "SEC_Filings", "confidence": 0.83, "primary": "Disclosure",
                     "key_evidence": {"supporting": [], "opposing": []}}
                ],
                "tertiary": [
                    {"label": "10-K", "confidence": 0.77, "primary": "Disclosure", "secondary": "SEC_Filings",
                     "key_evidence": {"supporting": [], "opposing": []}}
                ],
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

    # Mock Supabase client for tests
    fake_supabase = types.SimpleNamespace()

    # Create mock table responses
    class MockTable:
        def __init__(self, table_name):
            self.table_name = table_name
            self._data = self._get_mock_data()

        def _get_mock_data(self):
            if self.table_name == "retraining_data":
                # Return test data with sufficient documents per tag
                return [
                    {"id": i, "primary_tag_ids": [1], "secondary_tag_ids": [10], "tertiary_tag_ids": [100]}
                    for i in range(1, 201)  # 200 documents for Disclosure -> SEC_Filings -> 10-K
                ] + [
                    {"id": i, "primary_tag_ids": [2], "secondary_tag_ids": [20], "tertiary_tag_ids": [200]}
                    for i in range(201, 351)  # 150 documents for News -> Industry -> Energy
                ] + [
                    {"id": i, "primary_tag_ids": [3], "secondary_tag_ids": [30], "tertiary_tag_ids": [300]}
                    for i in range(351, 501)  # 150 documents for Recommendations -> Strategic -> M&A
                ]
            elif self.table_name == "tags":
                # Return test tag hierarchy
                return [
                    # Primary tags
                    {"id": 1, "tag_name": "Disclosure", "parent_id": None},
                    {"id": 2, "tag_name": "News", "parent_id": None},
                    {"id": 3, "tag_name": "Recommendations", "parent_id": None},
                    # Secondary tags
                    {"id": 10, "tag_name": "SEC_Filings", "parent_id": 1},
                    {"id": 20, "tag_name": "Industry", "parent_id": 2},
                    {"id": 30, "tag_name": "Strategic_Recommendations", "parent_id": 3},
                    # Tertiary tags
                    {"id": 100, "tag_name": "10-K", "parent_id": 10},
                    {"id": 200, "tag_name": "Energy", "parent_id": 20},
                    {"id": 300, "tag_name": "M&A_Rationale", "parent_id": 30},
                ]
            return []

        def select(self, *args):
            return self

        @property
        def not_(self):
            return self

        def is_(self, *args, **kwargs):
            return self

        def execute(self):
            return types.SimpleNamespace(data=self._data)

    def mock_table(table_name):
        return MockTable(table_name)

    fake_supabase.table = mock_table

    sys.path.insert(0, str(SERVICE_ROOT))
    import importlib
    app_mod = importlib.import_module("app")  # imports ai-service/app.py

    # Inject mock Supabase client
    app_mod.supabase = fake_supabase

    return app_mod

@pytest.fixture
def client(app_module):
    # FastAPI TestClient
    return TestClient(app_module.app)
