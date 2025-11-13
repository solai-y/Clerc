# app.py (AI service)
from pathlib import Path
import time
import re
import subprocess
import threading
import os
import sys
import logging
from typing import Any, Dict

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

import joblib

# Configure logging for better debugging in CI/CD
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s"
)
logger = logging.getLogger(__name__)

# Import train module (not specific function) so monkeypatching works in tests
import train

# Training configuration - must match train.py
MIN_DOCS_PER_TAG = 10

# Add parent directory to path to import shared utilities
# Works both locally (when run from ai-service dir) and in Docker (when shared_utils is copied)
parent_dir = Path(__file__).parent.parent
if parent_dir not in [Path(p) for p in sys.path]:
    sys.path.insert(0, str(parent_dir))
from shared_utils.text_preprocessing import clean_text

# Initialize Supabase client for validation endpoint
from supabase import create_client, Client
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None

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

# Rebuild status tracking (detailed state for frontend)
_rebuild_status = {
    "is_rebuilding": False,
    "status": "idle",  # idle, in_progress, completed, failed
    "message": "",
    "progress": 0,  # 0-100
    "error": None,
    "started_at": None,
    "completed_at": None,
    "duration_seconds": None
}
_rebuild_status_lock = threading.Lock()


# ------------------- Routes -------------------
@app.get("/e2e")
def health() -> Any:
    status = "ok" if best_model is not None else "model_unavailable"
    rebuilding = _rebuilding.is_set()
    return {"status": "AI Service is reachable", "model_status": status, "rebuilding": rebuilding}


@app.get("/rebuild/status")
def get_rebuild_status() -> Any:
    """
    Get detailed rebuild status including progress, success/failure, and error messages.
    Frontend should poll this instead of /health for accurate rebuild feedback.
    """
    with _rebuild_status_lock:
        return dict(_rebuild_status)


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
    Returns validation status and tag statistics dynamically from database.
    """
    import traceback
    import logging
    from collections import defaultdict

    logger = logging.getLogger(__name__)

    try:
        # Log validation start with current model status
        model_status = "ok" if best_model is not None else "not_loaded"
        model_version = getattr(best_model, "version", "unknown") if best_model else "none"
        logger.info(f"Validation called. Model status: {model_status}, version: {model_version}")

        # Check if Supabase client is initialized
        if not supabase:
            logger.error("Supabase client not configured")
            raise HTTPException(status_code=500, detail="Supabase client not configured")

        # Fetch tag IDs from retraining_data table (not document text to avoid timeout)
        logger.info("Fetching training data from retraining_data table")
        response = supabase.table("retraining_data") \
            .select("id,primary_tag_ids,secondary_tag_ids,tertiary_tag_ids") \
            .not_.is_("primary_tag_ids", "null") \
            .execute()

        documents = response.data
        logger.info(f"Fetched {len(documents)} documents from retraining_data")

        if not documents:
            logger.warning("No training documents found in retraining_data table")
            return {
                "valid": False,
                "total_documents": 0,
                "primary_tags": {},
                "secondary_tags": {},
                "tertiary_tags": {},
                "invalid_tags": [],
                "message": "No training data available"
            }

        # Fetch tags table to map IDs to names
        logger.info("Fetching tags from tags table")
        tags_response = supabase.table("tags").select("id,tag_name,parent_id").execute()
        tags_map = {tag['id']: {'name': tag['tag_name'], 'parent_id': tag['parent_id']} for tag in tags_response.data}
        logger.info(f"Loaded {len(tags_map)} tags from database")

        # Count documents per tag
        primary_counts = defaultdict(int)
        secondary_counts = defaultdict(int)
        tertiary_counts = defaultdict(int)

        for doc in documents:
            # Count primary tags
            if doc.get('primary_tag_ids'):
                for tag_id in doc['primary_tag_ids']:
                    if tag_id in tags_map:
                        tag_name = tags_map[tag_id]['name']
                        primary_counts[tag_name] += 1

            # Count secondary tags
            if doc.get('secondary_tag_ids'):
                for tag_id in doc['secondary_tag_ids']:
                    if tag_id in tags_map:
                        tag_name = tags_map[tag_id]['name']
                        secondary_counts[tag_name] += 1

            # Count tertiary tags
            if doc.get('tertiary_tag_ids'):
                for tag_id in doc['tertiary_tag_ids']:
                    if tag_id in tags_map:
                        tag_name = tags_map[tag_id]['name']
                        tertiary_counts[tag_name] += 1

        # Convert to regular dicts
        primary_counts = dict(primary_counts)
        secondary_counts = dict(secondary_counts)
        tertiary_counts = dict(tertiary_counts)

        logger.info(f"Tag counts - Primary: {len(primary_counts)}, Secondary: {len(secondary_counts)}, Tertiary: {len(tertiary_counts)}")

        # Check if any tag has fewer than MIN_DOCS_PER_TAG documents
        invalid_tags = []

        for tag, count in primary_counts.items():
            if count < MIN_DOCS_PER_TAG:
                invalid_tags.append({"level": "primary", "tag": tag, "count": count, "required": MIN_DOCS_PER_TAG})

        for tag, count in secondary_counts.items():
            if count < MIN_DOCS_PER_TAG:
                invalid_tags.append({"level": "secondary", "tag": tag, "count": count, "required": MIN_DOCS_PER_TAG})

        for tag, count in tertiary_counts.items():
            if count < MIN_DOCS_PER_TAG:
                invalid_tags.append({"level": "tertiary", "tag": tag, "count": count, "required": MIN_DOCS_PER_TAG})

        is_valid = len(invalid_tags) == 0

        if invalid_tags:
            logger.info(f"Validation failed: {len(invalid_tags)} tags below minimum - {invalid_tags}")
        else:
            logger.info("Validation passed: all tags meet minimum requirements")

        return {
            "valid": is_valid,
            "total_documents": len(documents),
            "primary_tags": primary_counts,
            "secondary_tags": secondary_counts,
            "tertiary_tags": tertiary_counts,
            "invalid_tags": invalid_tags,
            "message": "Training data is valid" if is_valid else f"Found {len(invalid_tags)} tags with fewer than {MIN_DOCS_PER_TAG} documents"
        }
    except HTTPException:
        # Re-raise HTTPException without wrapping
        raise
    except Exception as e:
        # Log full traceback for CI logs
        tb = traceback.format_exc()
        logger.error(f"Unhandled exception in /training/validate: {e}\n{tb}")
        # Return structured error so tests can show the cause
        raise HTTPException(status_code=500, detail=f"Internal validation error: {str(e)}. See server logs for traceback.")


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
        import datetime

        # Initialize status
        with _rebuild_status_lock:
            _rebuild_status.update({
                "is_rebuilding": True,
                "status": "in_progress",
                "message": "Starting rebuild...",
                "progress": 0,
                "error": None,
                "started_at": datetime.datetime.now().isoformat(),
                "completed_at": None,
                "duration_seconds": None
            })

        try:
            _rebuilding.set()
            t0 = time.time()

            # Step 1: Try to fetch CSV from retraining-service
            with _rebuild_status_lock:
                _rebuild_status["message"] = "Fetching training data from retraining-service..."

            print("Fetching training data from retraining-service...")
            retraining_service_url = os.getenv("RETRAINING_SERVICE_URL", "http://retraining-service:5009")
            csv_url = f"{retraining_service_url}/retraining/export-csv"

            import requests

            try:
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

                with _rebuild_status_lock:
                    _rebuild_status["message"] = f"Fetched {len(lines) - 1} training samples, preparing data..."

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

            except Exception as e:
                print(f"⚠ Failed to fetch training data from retraining-service: {e}")
                print("⚠ Will use existing training_data_text.csv for rebuild")
                with _rebuild_status_lock:
                    _rebuild_status["message"] = "Using existing training data (fetch failed), starting training..."
                # Continue with existing CSV - don't fail the rebuild

            # Step 6: Retrain (this runs train.py and saves to models_hier/)
            with _rebuild_status_lock:
                _rebuild_status["message"] = "Training models (this may take 1-2 minutes)..."

            print("Starting model training...")
            subprocess.run(["python", "train.py"], check=True)

            with _rebuild_status_lock:
                _rebuild_status["message"] = "Model training complete, loading new model..."

            # Step 7: Load new model - use train.build_best_model so test monkeypatching works
            new_model = train.build_best_model(MODELS_DIR)

            with _rebuild_status_lock:
                _rebuild_status["message"] = "Activating new model..."

            # Step 8: Atomic swap
            with _model_swap_lock:
                best_model = new_model

            elapsed = time.time() - t0
            model_version = getattr(new_model, "version", "unknown")
            print(f"✓ Rebuild complete in {elapsed:.2f}s - swapped to model version: {model_version}")

            # Mark as completed
            with _rebuild_status_lock:
                _rebuild_status.update({
                    "is_rebuilding": False,
                    "status": "completed",
                    "message": f"Rebuild completed successfully in {elapsed:.2f}s",
                    "progress": 100,
                    "completed_at": datetime.datetime.now().isoformat(),
                    "duration_seconds": round(elapsed, 2)
                })

        except requests.exceptions.RequestException as e:
            error_msg = f"Failed to fetch training data from retraining-service: {e}"
            print(f"✗ {error_msg}")
            with _rebuild_status_lock:
                _rebuild_status.update({
                    "is_rebuilding": False,
                    "status": "failed",
                    "message": "Rebuild failed",
                    "error": error_msg,
                    "progress": 0,
                    "completed_at": datetime.datetime.now().isoformat(),
                    "duration_seconds": round(time.time() - t0, 2) if 't0' in locals() else None
                })
        except ValueError as e:
            error_msg = f"CSV validation failed: {e}"
            print(f"✗ {error_msg}")
            with _rebuild_status_lock:
                _rebuild_status.update({
                    "is_rebuilding": False,
                    "status": "failed",
                    "message": "Rebuild failed",
                    "error": error_msg,
                    "progress": 0,
                    "completed_at": datetime.datetime.now().isoformat(),
                    "duration_seconds": round(time.time() - t0, 2) if 't0' in locals() else None
                })
        except Exception as e:
            error_msg = f"Rebuild failed: {e}"
            print(f"✗ {error_msg}")
            with _rebuild_status_lock:
                _rebuild_status.update({
                    "is_rebuilding": False,
                    "status": "failed",
                    "message": "Rebuild failed",
                    "error": str(e),
                    "progress": 0,
                    "completed_at": datetime.datetime.now().isoformat(),
                    "duration_seconds": round(time.time() - t0, 2) if 't0' in locals() else None
                })
        finally:
            _rebuilding.clear()

    threading.Thread(target=_do_rebuild, daemon=True).start()
    return {"status": "rebuild started"}


# ------------------- Entrypoint (dev) -------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5004)
