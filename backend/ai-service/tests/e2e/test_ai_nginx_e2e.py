import time
from pathlib import Path
from typing import Callable, Optional

import pytest
import requests

# -------------------------------------------------------------------
# Paths (resolve relative to this file)
# -------------------------------------------------------------------
# this file: …/backend/ai-service/tests/e2e/test_ai_nginx_e2e.py
AI_SERVICE_ROOT = Path(__file__).resolve().parents[2]      # …/backend/ai-service
DEFAULT_PDF = AI_SERVICE_ROOT / "shared" / "sample.pdf"    # …/backend/ai-service/shared/sample.pdf

# -------------------------------------------------------------------
# URLs (through nginx)
# -------------------------------------------------------------------
NGINX_BASE = "http://localhost"
AI_HEALTH_URL = f"{NGINX_BASE}/ai/v1/health"
AI_PREDICT_URL = f"{NGINX_BASE}/ai/v1/predict"

def _wait_for(
    url: str,
    ok: Optional[Callable[[requests.Response], bool]] = None,
    timeout_s: int = 60,
    interval_s: float = 1.0,
) -> None:
    """
    Poll `url` until it returns 200 (and optional `ok(resp)` is True) or timeout.
    """
    deadline = time.time() + timeout_s
    last_err = None
    while time.time() < deadline:
        try:
            r = requests.get(url, timeout=5)
            if r.status_code == 200 and (ok is None or ok(r)):
                return
            last_err = f"status={r.status_code} body={r.text[:200]}"
        except Exception as e:  # noqa: BLE001
            last_err = str(e)
        time.sleep(interval_s)
    raise RuntimeError(f"Service at {url} did not become ready: {last_err}")

def _health_ok(resp: requests.Response) -> bool:
    try:
        j = resp.json()
        return j.get("status") == "ok"
    except Exception:  # noqa: BLE001
        return False


def test_ai_predict_ok_via_nginx():
    # Ensure test PDF exists at the expected path
    assert DEFAULT_PDF.exists(), f"Test PDF not found at {DEFAULT_PDF}"

    # Wait for gateway (nginx -> ai-service) to be healthy
    _wait_for(AI_HEALTH_URL, ok=_health_ok, timeout_s=90)

    # Call /ai/v1/predict through nginx
    with DEFAULT_PDF.open("rb") as f:
        files = {"pdf": (DEFAULT_PDF.name, f, "application/pdf")}
        data = {"threshold_pct": "10"}
        resp = requests.post(AI_PREDICT_URL, files=files, data=data, timeout=30)

    # Basic response checks
    assert resp.status_code == 200, f"Non-200 from /predict: {resp.status_code} {resp.text}"
    j = resp.json()
    # Expected schema: filename + tags (list of objects with tag/score)
    assert "filename" in j, f"Missing 'filename' in response: {j}"
    assert "tags" in j and isinstance(j["tags"], list), f"Missing/invalid 'tags' in response: {j}"
    # Be tolerant of empty lists, but usually there should be at least one tag
    if j["tags"]:
        first = j["tags"][0]
        assert "tag" in first and "score" in first, f"Unexpected tag shape: {first}"
