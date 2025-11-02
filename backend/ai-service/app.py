# app.py (AI service)
from pathlib import Path
import time
import re
import subprocess
import threading
import os
import sys
from typing import Any, Dict

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

import joblib

# Import train module (not specific function) so monkeypatching works in tests
import train

# Add parent directory to path to import shared utilities
# Works both locally (when run from ai-service dir) and in Docker (when shared_utils is copied)
parent_dir = Path(__file__).parent.parent
if parent_dir not in [Path(p) for p in sys.path]:
    sys.path.insert(0, str(parent_dir))
from shared_utils.text_preprocessing import clean_text

MODELS_DIR = Path("models_hier")
PRIMARY_MODEL_PATH = MODELS_DIR / "primary.joblib"
BEST_MODEL_PATH = MODELS_DIR / "best_model.joblib"
LOCK_PATH = Path("/tmp/ai_train.lock")  # process-shared lock for workers

app = FastAPI()

# ------------------- Pydantic Models -------------------
class PredictRequest(BaseModel):
    text: str

# ------------------- Preprocessing -------------------
# Text preprocessing is now imported from shared_utils.text_preprocessing

# ------------------- Startup: ensure models exist -------------------
def _need_training() -> bool:
    # train.py writes multiple files; any one of these is enough to skip rebuild
    return not PRIMARY_MODEL_PATH.exists() or not BEST_MODEL_PATH.exists()

def _train_sync():
    MODELS_DIR.mkdir(exist_ok=True)
    print("No models detected; fetching latest data and training at startup...")

    # Fetch latest CSV from retraining-service before training
    try:
        import requests
        retraining_service_url = os.getenv("RETRAINING_SERVICE_URL", "http://retraining-service:5009")
        csv_url = f"{retraining_service_url}/retraining/export-csv"

        print(f"Fetching training data from {csv_url}...")
        response = requests.get(csv_url, timeout=120)
        response.raise_for_status()

        csv_content = response.text
        if not csv_content or len(csv_content.strip()) == 0:
            raise ValueError("Received empty CSV from retraining-service")

        lines = csv_content.strip().split('\n')
        if len(lines) < 2:
            raise ValueError(f"CSV has insufficient data: only {len(lines)} line(s)")

        print(f"✓ Fetched CSV with {len(lines) - 1} data rows")

        # Write CSV to training_data_text.csv
        training_csv_path = Path("./training_data_text.csv")
        with open(training_csv_path, 'w', encoding='utf-8') as f:
            f.write(csv_content)
        print(f"✓ Saved training data to {training_csv_path}")

    except Exception as e:
        print(f"⚠ Failed to fetch latest training data: {e}")
        print("⚠ Will use existing training_data_text.csv if available")

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
        best_model = train.build_best_model(MODELS_DIR)
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
        raw_result = model.predict([processed_text])[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {e}")
    elapsed = time.time() - t0

    # Transform multi-class result to prediction service format (multi-label support)
    # The model returns: {'primary': [{label, confidence, key_evidence}, ...], 'secondary': [...], 'tertiary': [...]}
    # Prediction service expects arrays: {'primary': [{label, confidence, key_evidence}, ...], ...}

    transformed_result = {}

    for level in ['primary', 'secondary', 'tertiary']:
        if level in raw_result and isinstance(raw_result[level], list) and len(raw_result[level]) > 0:
            # Return ALL predictions for multi-label support (not just top one)
            predictions_for_level = []

            for pred in raw_result[level]:
                predictions_for_level.append({
                    "label": pred.get('label', ''),
                    "confidence": pred.get('confidence', 0.0),
                    "key_evidence": pred.get('key_evidence', {}),
                    # Include primary/secondary context for child levels
                    "primary": pred.get('primary'),
                    "secondary": pred.get('secondary'),
                })

            transformed_result[level] = predictions_for_level

    # Include model_version if present in raw_result
    if 'model_version' in raw_result:
        transformed_result['model_version'] = raw_result['model_version']

    # Also include the raw multi-class predictions for the frontend
    return {
        "prediction": transformed_result,
        "raw_predictions": raw_result,  # Keep full multi-class data for frontend
        "elapsed_seconds": round(elapsed, 6),
        "processed_text": processed_text
    }


@app.get("/training/validate")
def validate_training_data() -> Any:
    """
    Validate that training data meets minimum requirements before retraining.
    Returns validation status and tag statistics.
    """
    import pandas as pd

    try:
        # Read training data
        df = pd.read_csv("./training_data_text.csv")
        df = df.dropna(subset=["text"]).reset_index(drop=True)

        # Count documents per tag at each level
        from collections import defaultdict

        primary_counts = df["primary"].value_counts().to_dict()
        secondary_counts = df["secondary"].value_counts().to_dict()
        tertiary_counts = df["tertiary"].value_counts().to_dict()

        # Check if any tag has fewer than 10 documents
        MIN_DOCS = 10
        invalid_tags = []

        for tag, count in primary_counts.items():
            if count < MIN_DOCS:
                invalid_tags.append({"level": "primary", "tag": tag, "count": count, "required": MIN_DOCS})

        for tag, count in secondary_counts.items():
            if count < MIN_DOCS:
                invalid_tags.append({"level": "secondary", "tag": tag, "count": count, "required": MIN_DOCS})

        for tag, count in tertiary_counts.items():
            if count < MIN_DOCS:
                invalid_tags.append({"level": "tertiary", "tag": tag, "count": count, "required": MIN_DOCS})

        is_valid = len(invalid_tags) == 0

        return {
            "valid": is_valid,
            "total_documents": len(df),
            "primary_tags": primary_counts,
            "secondary_tags": secondary_counts,
            "tertiary_tags": tertiary_counts,
            "invalid_tags": invalid_tags,
            "message": "Training data is valid" if is_valid else f"Found {len(invalid_tags)} tags with fewer than {MIN_DOCS} documents"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to validate training data: {e}")


@app.post("/rebuild", status_code=202)
def rebuild() -> Any:
    """
    Trigger a rebuild of the model in the background.
    Fetches latest training data from retraining-service, then trains.
    Requests keep using the old model until the swap is complete.
    """
    if _rebuilding.is_set():
        return JSONResponse(content={"status": "already rebuilding"}, status_code=202)

    def _do_rebuild():
        global best_model
        try:
            _rebuilding.set()
            t0 = time.time()

            # Step 1: Fetch CSV from retraining-service
            print("Fetching training data from retraining-service...")
            retraining_service_url = os.getenv("RETRAINING_SERVICE_URL", "http://retraining-service:5009")
            csv_url = f"{retraining_service_url}/retraining/export-csv"

            import requests
            response = requests.get(csv_url, timeout=60)
            response.raise_for_status()

            # Step 2: Validate CSV has data
            csv_content = response.text
            if not csv_content or len(csv_content.strip()) == 0:
                raise ValueError("Received empty CSV from retraining-service")

            lines = csv_content.strip().split('\n')
            if len(lines) < 2:
                raise ValueError(f"CSV has insufficient data: only {len(lines)} line(s)")

            # Step 3: Validate CSV header
            expected_columns = {'primary', 'secondary', 'tertiary', 'text'}
            header = lines[0].split(',')
            header_set = {col.strip() for col in header}
            if not expected_columns.issubset(header_set):
                raise ValueError(f"CSV header missing required columns. Expected: {expected_columns}, Got: {header_set}")

            print(f"✓ Fetched CSV with {len(lines) - 1} data rows")

            # Step 4: Backup existing training data (optional safety)
            training_csv_path = Path("./training_data_text.csv")
            if training_csv_path.exists():
                backup_path = Path("./training_data_text.csv.backup")
                import shutil
                shutil.copy2(training_csv_path, backup_path)
                print(f"✓ Backed up existing training data to {backup_path}")

            # Step 5: Write new CSV
            with open(training_csv_path, 'w', encoding='utf-8') as f:
                f.write(csv_content)
            print(f"✓ Saved training data to {training_csv_path}")

            # Step 6: Retrain (this runs train.py and saves to models_hier/)
            print("Starting model training...")
            subprocess.run(["python", "train.py"], check=True)

            # Step 7: Load new model - use train.build_best_model so test monkeypatching works
            new_model = train.build_best_model(MODELS_DIR)

            # Step 8: Atomic swap
            with _model_swap_lock:
                best_model = new_model

            elapsed = time.time() - t0
            model_version = getattr(new_model, "version", "unknown")
            print(f"✓ Rebuild complete in {elapsed:.2f}s - swapped to model version: {model_version}")
        except requests.exceptions.RequestException as e:
            print(f"✗ Failed to fetch training data from retraining-service: {e}")
        except ValueError as e:
            print(f"✗ CSV validation failed: {e}")
        except Exception as e:
            print(f"✗ Rebuild failed: {e}")
        finally:
            _rebuilding.clear()

    threading.Thread(target=_do_rebuild, daemon=True).start()
    return {"status": "rebuild started"}


# ------------------- Entrypoint (dev) -------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5004)
