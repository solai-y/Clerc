# app.py (AI service)
from pathlib import Path
import time
import re
import subprocess
import threading
import os
from typing import Any, Dict

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

import joblib
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS

# Import your wrapper class + loader
from train import build_best_model

MODELS_DIR = Path("models_hier")
PRIMARY_MODEL_PATH = MODELS_DIR / "primary.joblib"
BEST_MODEL_PATH = MODELS_DIR / "best_model.joblib"
LOCK_PATH = Path("/tmp/ai_train.lock")  # process-shared lock for workers

app = FastAPI()

# ------------------- Pydantic Models -------------------
class PredictRequest(BaseModel):
    text: str

# ------------------- Preprocessing -------------------
def clean_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z\s]", " ", text)
    tokens = [tok for tok in text.split() if tok not in ENGLISH_STOP_WORDS]
    return " ".join(tokens)

# ------------------- Startup: ensure models exist -------------------
def _need_training() -> bool:
    # train.py writes multiple files; any one of these is enough to skip rebuild
    return not PRIMARY_MODEL_PATH.exists() or not BEST_MODEL_PATH.exists()

def _train_sync():
    MODELS_DIR.mkdir(exist_ok=True)
    print("No models detected; running training once at startup...")
    # Call the training script; raise if it fails
    subprocess.run(["python", "train.py"], check=True)
    print("Initial training complete.")

def _with_file_lock(lock_path: Path, fn):
    """
    Cross-process lock using fcntl (Linux). Ensures only one worker trains.
    Other workers wait here until the lock is released.
    """
    import fcntl
    lock_fd = os.open(str(lock_path), os.O_CREAT | os.O_RDWR)
    try:
        fcntl.flock(lock_fd, fcntl.LOCK_EX)
        return fn()
    finally:
        try:
            fcntl.flock(lock_fd, fcntl.LOCK_UN)
        finally:
            os.close(lock_fd)

def ensure_models_ready():
    if not _need_training():
        return
    # Only one worker/process should perform training
    def _do():
        # Re-check inside the lock to avoid TOCTTOU
        if _need_training():
            _train_sync()
    _with_file_lock(LOCK_PATH, _do)

# ------------------- Model state -------------------
best_model = None

# Run at module import to ensure models are ready for tests
try:
    ensure_models_ready()
except Exception as e:
    # Fail fast & loud: API will still start, but /predict will return 503 until /rebuild succeeds
    print(f"Auto-training at startup failed: {e}")

# Load models after ensuring they exist
if BEST_MODEL_PATH.exists() or PRIMARY_MODEL_PATH.exists():
    try:
        best_model = build_best_model(MODELS_DIR)
    except Exception as e:
        print(f"Failed to load models: {e}")
else:
    print("Models not found; waiting for /rebuild to succeed.")

# Synchronization primitives
_model_swap_lock = threading.Lock()
_rebuilding = threading.Event()  # True while rebuilding


# ------------------- Routes -------------------
@app.get("/e2e")
def health() -> Any:
    status = "ok" if best_model is not None else "model_unavailable"
    rebuilding = _rebuilding.is_set()
    return {"status": "AI Service is reachable", "model_status": status, "rebuilding": rebuilding}


@app.post("/predict")
async def predict(request: PredictRequest) -> Any:
    if best_model is None:
        raise HTTPException(status_code=503, detail="Model not loaded. Try again after /rebuild finishes.")

    raw_text = request.text
    if not raw_text or not raw_text.strip():
        raise HTTPException(status_code=400, detail="'text' must be a non-empty string.")

    processed_text = clean_text(raw_text)

    t0 = time.time()
    try:
        with _model_swap_lock:
            model = best_model
        result = model.predict([processed_text])[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {e}")
    elapsed = time.time() - t0

    return {
        "prediction": result,
        "elapsed_seconds": round(elapsed, 6),
        "processed_text": processed_text
    }


@app.post("/rebuild", status_code=202)
def rebuild() -> Any:
    """
    Trigger a rebuild of the model in the background.
    Requests keep using the old model until the swap is complete.
    """
    if _rebuilding.is_set():
        return JSONResponse(content={"status": "already rebuilding"}, status_code=202)

    def _do_rebuild():
        global best_model
        try:
            _rebuilding.set()
            t0 = time.time()
            # retrain (this runs train.py and saves to models_hier/)
            subprocess.run(["python", "train.py"], check=True)
            # load new model
            new_model = build_best_model(MODELS_DIR)
            # atomic swap
            with _model_swap_lock:
                best_model = new_model
            elapsed = time.time() - t0
            print(f"Rebuild complete in {elapsed:.2f}s")
        except Exception as e:
            print(f"Rebuild failed: {e}")
        finally:
            _rebuilding.clear()

    threading.Thread(target=_do_rebuild, daemon=True).start()
    return {"status": "rebuild started"}


# ------------------- Entrypoint (dev) -------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5004)
