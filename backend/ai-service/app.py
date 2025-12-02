# app.py (AI service)
from pathlib import Path
import time
import subprocess
import threading
import os
import sys
import logging
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

import joblib  # noqa: F401

# Configure logging for better debugging in CI/CD
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger(__name__)

# Import train module (not specific function) so monkeypatching works in tests
import train

# Training configuration - must match train.py
MIN_DOCS_PER_TAG = 10

# Add parent directory to path to import shared utilities
parent_dir = Path(__file__).parent.parent
if parent_dir not in [Path(p) for p in sys.path]:
    sys.path.insert(0, str(parent_dir))
from shared_utils.text_preprocessing import clean_text  # noqa: E402

# Initialize Supabase client for validation endpoint
from supabase import create_client, Client  # noqa: E402
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None

MODELS_DIR = Path("models_hier")
PRIMARY_MODEL_PATH = MODELS_DIR / "primary.joblib"
BEST_MODEL_PATH = MODELS_DIR / "best_model.joblib"
LOCK_PATH = Path("/tmp/ai_train.lock")  # process-shared lock for workers

app = FastAPI()

# ------------------- Pydantic Models (for clean OpenAPI) -------------------
class PredictRequest(BaseModel):
    text: str = Field(..., example="Quarterly report: revenue grew 12% ...")

class HealthResponse(BaseModel):
    status: str = Field(..., example="AI Service is reachable")
    model_status: str = Field(..., example="ok")
    rebuilding: bool = Field(..., example=False)

class RebuildStatus(BaseModel):
    is_rebuilding: bool = Field(..., example=False)
    status: str = Field(..., example="idle")  # idle, in_progress, completed, failed
    message: str = Field(..., example="Ready")
    progress: int = Field(..., example=0)
    error: Optional[str] = Field(None, example=None)
    started_at: Optional[str] = Field(None, example="2025-01-01T12:34:56.000Z")
    completed_at: Optional[str] = Field(None, example=None)
    duration_seconds: Optional[float] = Field(None, example=12.34)

class PredictionItem(BaseModel):
    label: str = Field(..., example="Buy")
    confidence: float = Field(..., example=0.93)
    key_evidence: Optional[Dict[str, Any]] = Field(None, example={"span": "…text…"})
    primary: Optional[str] = Field(None, example="Recommendation")
    secondary: Optional[str] = Field(None, example="Equity")

class PredictionLevels(BaseModel):
    # default_factory keeps schema as arrays and avoids mutable default warnings
    primary: List[PredictionItem] = Field(default_factory=list)
    secondary: List[PredictionItem] = Field(default_factory=list)
    tertiary: List[PredictionItem] = Field(default_factory=list)
    model_version: Optional[str] = Field(None, example="2025-03-01_12-00")

class PredictResponse(BaseModel):
    prediction: PredictionLevels = Field(
        ...,
        example={
            "primary": [{"label": "Buy", "confidence": 0.93, "key_evidence": {}, "primary": "Recommendation"}],
            "secondary": [],
            "tertiary": [],
            "model_version": "2025-03-01_12-00",
        },
    )
    raw_predictions: Any = Field(..., example={"primary": [{"label": "Buy", "confidence": 0.93}]})
    elapsed_seconds: float = Field(..., example=0.012345)
    processed_text: str = Field(..., example="quarterly report revenue grew 12 ...")

class TrainingValidateResponse(BaseModel):
    valid: bool = Field(..., example=True)
    total_documents: int = Field(..., example=42)
    # >>> key change: give Dict fields default_factory + concrete examples
    primary_tags: Dict[str, int] = Field(
        default_factory=dict,
        example={"Recommendation": 15, "Earnings": 27}
    )
    secondary_tags: Dict[str, int] = Field(
        default_factory=dict,
        example={"Healthcare": 11, "Technology": 8}
    )
    tertiary_tags: Dict[str, int] = Field(
        default_factory=dict,
        example={"AI": 5, "Pricing": 3}
    )
    invalid_tags: List[Dict[str, Any]] = Field(
        default_factory=list,
        example=[{"level": "primary", "tag": "IPO", "count": 6, "required": 10}]
    )
    message: str = Field(..., example="Training data is valid")

class SimpleStatus(BaseModel):
    status: str = Field(..., example="rebuild started")
# ---------------------------------------------------------------------------

# ------------------- Startup: ensure models exist -------------------
def _need_training() -> bool:
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

        lines = csv_content.strip().split("\n")
        if len(lines) < 2:
            raise ValueError(f"CSV has insufficient data: only {len(lines)} line(s)")

        print(f"✓ Fetched CSV with {len(lines) - 1} data rows")

        training_csv_path = Path("./training_data_text.csv")
        with open(training_csv_path, "w", encoding="utf-8") as f:
            f.write(csv_content)
        print(f"✓ Saved training data to {training_csv_path}")

    except Exception as e:
        print(f"⚠ Failed to fetch latest training data: {e}")
        print("⚠ Will use existing training_data_text.csv if available")

    subprocess.run(["python", "train.py"], check=True)
    print("Initial training complete.")

def _with_file_lock(lock_path: Path, fn):
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
    def _do():
        if _need_training():
            _train_sync()
    _with_file_lock(LOCK_PATH, _do)

# ------------------- Model state -------------------
best_model = None
try:
    ensure_models_ready()
except Exception as e:
    print(f"Auto-training at startup failed: {e}")

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
    "status": "idle",
    "message": "",
    "progress": 0,
    "error": None,
    "started_at": None,
    "completed_at": None,
    "duration_seconds": None,
}
_rebuild_status_lock = threading.Lock()

# ------------------- Routes -------------------
@app.get("/e2e", response_model=HealthResponse)
def health() -> Any:
    status = "ok" if best_model is not None else "model_unavailable"
    rebuilding = _rebuilding.is_set()
    return {"status": "AI Service is reachable", "model_status": status, "rebuilding": rebuilding}

@app.get("/rebuild/status", response_model=RebuildStatus)
def get_rebuild_status() -> Any:
    with _rebuild_status_lock:
        return dict(_rebuild_status)

@app.post(
    "/predict",
    response_model=PredictResponse,
    responses={
        200: {
            "description": "Successful Response",
            "content": {
                "application/json": {
                    "example": {
                        "prediction": {
                            "primary": [{"label": "Buy", "confidence": 0.93, "key_evidence": {}, "primary": "Recommendation"}],
                            "secondary": [],
                            "tertiary": [],
                            "model_version": "2025-03-01_12-00",
                        },
                        "raw_predictions": {"primary": [{"label": "Buy", "confidence": 0.93}]},
                        "elapsed_seconds": 0.012345,
                        "processed_text": "quarterly report revenue grew 12 ..."
                    }
                }
            },
        }
    },
)
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

    transformed_result: Dict[str, Any] = {}
    for level in ["primary", "secondary", "tertiary"]:
        if level in raw_result and isinstance(raw_result[level], list) and len(raw_result[level]) > 0:
            predictions_for_level = []
            for pred in raw_result[level]:
                predictions_for_level.append({
                    "label": pred.get("label", ""),
                    "confidence": pred.get("confidence", 0.0),
                    "key_evidence": pred.get("key_evidence", {}),
                    "primary": pred.get("primary"),
                    "secondary": pred.get("secondary"),
                })
            transformed_result[level] = predictions_for_level

    if "model_version" in raw_result:
        transformed_result["model_version"] = raw_result["model_version"]

    return {
        "prediction": transformed_result,
        "raw_predictions": raw_result,
        "elapsed_seconds": round(elapsed, 6),
        "processed_text": processed_text,
    }

@app.get("/training/validate", response_model=TrainingValidateResponse)
def validate_training_data() -> Any:
    """
    Validate that training data meets minimum requirements before retraining.
    Returns validation status and tag statistics dynamically from database.
    """
    import traceback
    from collections import defaultdict

    try:
        model_status = "ok" if best_model is not None else "not_loaded"
        model_version = getattr(best_model, "version", "unknown") if best_model else "none"
        logger.info(f"Validation called. Model status: {model_status}, version: {model_version}")

        if not supabase:
            logger.error("Supabase client not configured")
            raise HTTPException(status_code=500, detail="Supabase client not configured")

        response = supabase.table("retraining_data") \
            .select("id,primary_tag_ids,secondary_tag_ids,tertiary_tag_ids") \
            .not_.is_("primary_tag_ids", "null") \
            .execute()

        documents = response.data
        logger.info(f"Fetched {len(documents)} documents from retraining_data")

        if not documents:
            return {
                "valid": False,
                "total_documents": 0,
                "primary_tags": {},
                "secondary_tags": {},
                "tertiary_tags": {},
                "invalid_tags": [],
                "message": "No training data available",
            }

        tags_response = supabase.table("tags").select("id,tag_name,parent_id").execute()
        tags_map = {tag["id"]: {"name": tag["tag_name"], "parent_id": tag["parent_id"]} for tag in tags_response.data}

        # Initialize counts with all tags set to 0
        # This ensures tags with 0 documents are included in validation
        primary_counts = defaultdict(int)
        secondary_counts = defaultdict(int)
        tertiary_counts = defaultdict(int)

        # Pre-populate all tags with 0 count based on their hierarchy level
        for tag_id, tag_info in tags_map.items():
            tag_name = tag_info['name']
            parent_id = tag_info['parent_id']

            if parent_id is None:
                # Primary tag (no parent)
                primary_counts[tag_name] = 0
            else:
                # Check if parent has a parent to determine if secondary or tertiary
                parent_info = tags_map.get(parent_id)
                if parent_info and parent_info['parent_id'] is None:
                    # Parent is primary, so this is secondary
                    secondary_counts[tag_name] = 0
                else:
                    # Parent is secondary, so this is tertiary
                    tertiary_counts[tag_name] = 0

        # Count documents per tag
        for doc in documents:
            if doc.get("primary_tag_ids"):
                for tag_id in doc["primary_tag_ids"]:
                    if tag_id in tags_map:
                        primary_counts[tags_map[tag_id]["name"]] += 1
            if doc.get("secondary_tag_ids"):
                for tag_id in doc["secondary_tag_ids"]:
                    if tag_id in tags_map:
                        secondary_counts[tags_map[tag_id]["name"]] += 1
            if doc.get("tertiary_tag_ids"):
                for tag_id in doc["tertiary_tag_ids"]:
                    if tag_id in tags_map:
                        tertiary_counts[tags_map[tag_id]["name"]] += 1

        primary_counts = dict(primary_counts)
        secondary_counts = dict(secondary_counts)
        tertiary_counts = dict(tertiary_counts)

        invalid_tags: List[Dict[str, Any]] = []
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

        return {
            "valid": is_valid,
            "total_documents": len(documents),
            "primary_tags": primary_counts,
            "secondary_tags": secondary_counts,
            "tertiary_tags": tertiary_counts,
            "invalid_tags": invalid_tags,
            "message": "Training data is valid" if is_valid else f"Found {len(invalid_tags)} tags with fewer than {MIN_DOCS_PER_TAG} documents",
        }
    except HTTPException:
        raise
    except Exception as e:
        tb = traceback.format_exc()
        logger.error(f"Unhandled exception in /training/validate: {e}\n{tb}")
        raise HTTPException(status_code=500, detail=f"Internal validation error: {str(e)}. See server logs for traceback.")

@app.post(
    "/rebuild",
    status_code=202,
    response_model=SimpleStatus,
    responses={
        202: {
            "description": "Accepted — rebuild kicked off",
            "content": {"application/json": {"example": {"status": "rebuild started"}}},
        }
    },
)
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
        with _rebuild_status_lock:
            _rebuild_status.update({
                "is_rebuilding": True,
                "status": "in_progress",
                "message": "Starting rebuild...",
                "progress": 0,
                "error": None,
                "started_at": datetime.datetime.now().isoformat(),
                "completed_at": None,
                "duration_seconds": None,
            })
        try:
            _rebuilding.set()
            t0 = time.time()

            # Step 1: Fetch CSV
            with _rebuild_status_lock:
                _rebuild_status["message"] = "Fetching training data from retraining-service..."
            import requests
            retraining_service_url = os.getenv("RETRAINING_SERVICE_URL", "http://retraining-service:5009")
            csv_url = f"{retraining_service_url}/retraining/export-csv"
            try:
                response = requests.get(csv_url, timeout=60)
                response.raise_for_status()
                csv_content = response.text
                if not csv_content or len(csv_content.strip()) == 0:
                    raise ValueError("Received empty CSV from retraining-service")
                lines = csv_content.strip().split("\n")
                if len(lines) < 2:
                    raise ValueError(f"CSV has insufficient data: only {len(lines)} line(s)")
                from shutil import copy2
                training_csv_path = Path("./training_data_text.csv")
                if training_csv_path.exists():
                    copy2(training_csv_path, Path("./training_data_text.csv.backup"))
                with open(training_csv_path, "w", encoding="utf-8") as f:
                    f.write(csv_content)
            except Exception as e:
                print(f"⚠ Failed to fetch training data from retraining-service: {e}")
                with _rebuild_status_lock:
                    _rebuild_status["message"] = "Using existing training data (fetch failed), starting training..."

            # Step 2: Train
            with _rebuild_status_lock:
                _rebuild_status["message"] = "Training models (this may take 1-2 minutes)..."
            subprocess.run(["python", "train.py"], check=True)

            with _rebuild_status_lock:
                _rebuild_status["message"] = "Model training complete, loading new model..."

            # Step 3: Load & swap
            new_model = train.build_best_model(MODELS_DIR)
            with _rebuild_status_lock:
                _rebuild_status["message"] = "Activating new model..."
            with _model_swap_lock:
                best_model = new_model

            elapsed = time.time() - t0
            with _rebuild_status_lock:
                _rebuild_status.update({
                    "is_rebuilding": False,
                    "status": "completed",
                    "message": f"Rebuild completed successfully in {elapsed:.2f}s",
                    "progress": 100,
                    "completed_at": datetime.datetime.now().isoformat(),
                    "duration_seconds": round(elapsed, 2),
                })
        except Exception as e:
            with _rebuild_status_lock:
                _rebuild_status.update({
                    "is_rebuilding": False,
                    "status": "failed",
                    "message": "Rebuild failed",
                    "error": str(e),
                    "progress": 0,
                    "completed_at": datetime.datetime.now().isoformat(),
                })
        finally:
            _rebuilding.clear()

    threading.Thread(target=_do_rebuild, daemon=True).start()
    return {"status": "rebuild started"}

# ------------------- Entrypoint (dev) -------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5004)
