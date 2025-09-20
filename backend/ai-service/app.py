# app.py (AI service)
from pathlib import Path
import time
import re
import subprocess
import threading
import os
from typing import Any, Dict

from flask import Flask, request, jsonify
from werkzeug.exceptions import BadRequest

import joblib
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS

# Import your wrapper class + loader
from train import build_best_model

MODELS_DIR = Path("models_hier")
PRIMARY_MODEL_PATH = MODELS_DIR / "primary.joblib"
BEST_MODEL_PATH = MODELS_DIR / "best_model.joblib"
LOCK_PATH = Path("/tmp/ai_train.lock")  # process-shared lock for gunicorn workers

app = Flask(__name__)

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
    app.logger.info("No models detected; running training once at startup...")
    # Call the training script; raise if it fails
    subprocess.run(["python", "train.py"], check=True)
    app.logger.info("Initial training complete.")

def _with_file_lock(lock_path: Path, fn):
    """
    Cross-process lock using fcntl (Linux). Ensures only one Gunicorn worker trains.
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

# Run at import time (before first request)
try:
    ensure_models_ready()
except Exception as e:
    # Fail fast & loud: API will still start, but /predict will return 503 until /rebuild succeeds
    app.logger.error(f"Auto-training at startup failed: {e}")

# ------------------- Model state -------------------
# After ensure_models_ready(), models should exist. If not, we’ll handle below.
best_model = None
if BEST_MODEL_PATH.exists() or PRIMARY_MODEL_PATH.exists():
    try:
        best_model = build_best_model(MODELS_DIR)
    except Exception as e:
        app.logger.error(f"Failed to load models: {e}")
else:
    app.logger.warning("Models not found; waiting for /rebuild to succeed.")

# Synchronization primitives
_model_swap_lock = threading.Lock()
_rebuilding = threading.Event()  # True while rebuilding


# ------------------- Routes -------------------
@app.route("/e2e", methods=["GET"])
def health() -> Any:
    status = "ok" if best_model is not None else "model_unavailable"
    rebuilding = _rebuilding.is_set()
    return jsonify({"status": "AI Service is reachable", "model_status": status, "rebuilding": rebuilding}), 200


@app.route("/predict", methods=["POST"])
def predict() -> Any:
    if best_model is None:
        return jsonify({"error": "Model not loaded. Try again after /rebuild finishes."}), 503

    try:
        data: Dict[str, Any] = request.get_json(force=True, silent=False)
    except BadRequest:
        return jsonify({"error": "Invalid JSON."}), 400

    if not isinstance(data, dict) or "text" not in data:
        return jsonify({"error": "Missing required field 'text'."}), 400

    raw_text = data["text"]
    if not isinstance(raw_text, str) or not raw_text.strip():
        return jsonify({"error": "'text' must be a non-empty string."}), 400

    processed_text = clean_text(raw_text)

    t0 = time.time()
    try:
        with _model_swap_lock:
            model = best_model
        result = model.predict([processed_text])[0]
    except Exception as e:
        return jsonify({"error": f"Prediction failed: {e}"}), 500
    elapsed = time.time() - t0

    return jsonify({
        "prediction": result,
        "elapsed_seconds": round(elapsed, 6),
        "processed_text": processed_text
    }), 200


@app.route("/rebuild", methods=["POST"])
def rebuild() -> Any:
    """
    Trigger a rebuild of the model in the background.
    Requests keep using the old model until the swap is complete.
    """
    if _rebuilding.is_set():
        return jsonify({"status": "already rebuilding"}), 202

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
            app.logger.info(f"Rebuild complete in {elapsed:.2f}s")
        except Exception as e:
            app.logger.error(f"Rebuild failed: {e}")
        finally:
            _rebuilding.clear()

    threading.Thread(target=_do_rebuild, daemon=True).start()
    return jsonify({"status": "rebuild started"}), 202


# ------------------- Entrypoint (dev) -------------------
if __name__ == "__main__":
    # In production, run with gunicorn:
    # gunicorn -w 2 -k gthread -t 300 -b 0.0.0.0:5004 app:app
    app.run(host="0.0.0.0", port=5004, debug=False, threaded=True)
