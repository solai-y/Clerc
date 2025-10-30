import os
import pytest

# Try importing the FastAPI app for in-process integration tests
try:
    from app import app as fastapi_app
    from fastapi.testclient import TestClient
except Exception:
    fastapi_app = None
    TestClient = None


@pytest.fixture(scope="session")
def base_url() -> str:
    # Running container’s exposed port (your docker-compose maps 5007:5007)
    return os.environ.get("TAGS_BASE_URL", "http://localhost:5007")


@pytest.fixture(scope="session")
def live_service_available(base_url: str) -> bool:
    """Ping a read-only endpoint to confirm the service is up."""
    import requests
    for path in ("/tags", "/tags/hierarchy", "/health", "/"):
        try:
            r = requests.get(f"{base_url}{path}", timeout=2)
            if r.status_code < 500:
                return True
        except Exception:
            pass
    return False


@pytest.fixture(scope="session")
def client():
    """
    FastAPI TestClient for integration tests.
    If the app cannot be imported (e.g., running only via docker), test is skipped.
    """
    if fastapi_app is None or TestClient is None:
        pytest.skip("FastAPI app not importable for integration tests.")
    with TestClient(fastapi_app) as c:
        yield c
