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
def _importance_sample(text: str, max_words: int) -> str:
    """
    Sample text by sentence importance scoring for very long documents.

    Scores sentences based on:
    - Financial keywords (revenue, earnings, profit, etc.)
    - Entity keywords (company names, inc, corp, etc.)
    - Action keywords (announced, reported, filed, etc.)
    - Numeric data (financial figures)
    - Capitalized words (named entities)

    Args:
        text: Input text to sample
        max_words: Maximum words to return

    Returns:
        String containing most important sentences up to max_words
    """
    # Keywords for importance scoring
    financial_kw = ['revenue', 'earnings', 'profit', 'loss', 'quarter', 'year',
                    'growth', 'margin', 'ebitda', 'cash', 'debt', 'sales', 'income']
    entity_kw = ['inc', 'corp', 'company', 'ltd', 'llc', 'corporation']
    action_kw = ['announced', 'reported', 'filed', 'disclosed', 'stated',
                 'released', 'published', 'showed', 'increased', 'decreased']

    all_keywords = financial_kw + entity_kw + action_kw

    # Split into sentences
    sentences = re.split(r'(?<=[.!?])\s+', text)

    # Score each sentence
    scored_sentences = []
    for sent in sentences:
        if not sent.strip():
            continue

        sent_lower = sent.lower()
        score = 0.0

        # Keyword matching (main scoring factor)
        for kw in all_keywords:
            score += sent_lower.count(kw)

        # Bonus for numbers (likely financial data)
        score += len(re.findall(r'\b\d+(?:,\d+)*(?:\.\d+)?%?\b', sent)) * 0.5

        # Bonus for capitalized words (named entities, companies, people)
        score += len(re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', sent)) * 0.3

        scored_sentences.append((score, sent))

    # Sort by score descending (highest importance first)
    scored_sentences.sort(reverse=True, key=lambda x: x[0])

    # Select top sentences up to max_words
    selected = []
    current_words = 0

    for score, sent in scored_sentences:
        sent_word_count = len(sent.split())
        if current_words + sent_word_count <= max_words:
            selected.append(sent)
            current_words += sent_word_count

        if current_words >= max_words:
            break

    return " ".join(selected)


def clean_text(text: str, max_words: int = 5000) -> str:
    """
    Clean and preprocess text for classification using dynamic sampling strategy.

    Strategy selection based on document length:
    - ≤ 5,000 words (57.5% of docs): No sampling, use full text
    - 5,001 - 20,000 words (25.9% of docs): Weighted beginning-heavy sampling (70/20/10)
    - > 20,000 words (16.6% of docs): Importance-based sentence scoring

    Args:
        text: Input text to clean
        max_words: Maximum number of words to process (default 5000 for performance)

    Returns:
        Cleaned and preprocessed text ready for classification
    """
    words = text.split()
    word_count = len(words)

    # Strategy selection based on document length
    if word_count <= max_words:
        # No sampling needed for short/medium documents
        sampled_text = text
        strategy = "none"

    elif word_count <= 20000:
        # Strategy 1: Weighted beginning-heavy sampling for long documents
        # 70% from beginning, 20% from middle, 10% from end
        beginning_size = int(max_words * 0.7)  # 3,500 words
        middle_size = int(max_words * 0.2)     # 1,000 words
        end_size = max_words - beginning_size - middle_size  # 500 words

        beginning = words[:beginning_size]
        middle_start = word_count // 2 - middle_size // 2
        middle = words[middle_start:middle_start + middle_size]
        end = words[-end_size:]

        sampled_text = " ".join(beginning + middle + end)
        strategy = "weighted"

    else:
        # Strategy 2: Importance-based sampling for very long documents
        # Uses keyword density and sentence scoring
        sampled_text = _importance_sample(text, max_words)
        strategy = "importance"

    # Log sampling strategy used (useful for monitoring)
    print(f"[clean_text] Document: {word_count:,} words → Strategy: {strategy} → Sampled: {len(sampled_text.split()):,} words")

    # Apply text cleaning to sampled text
    sampled_text = sampled_text.lower()
    sampled_text = re.sub(r"[^a-z\s]", " ", sampled_text)
    tokens = [tok for tok in sampled_text.split() if tok not in ENGLISH_STOP_WORDS]

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
        raw_result = model.predict([processed_text])[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {e}")
    elapsed = time.time() - t0

    # Transform multi-class result to prediction service format
    # The model returns: {'primary': [{label, confidence, key_evidence}, ...], 'secondary': [...], 'tertiary': [...]}
    # Prediction service expects: {'primary': {pred, confidence, reasoning, key_evidence}, ...}

    transformed_result = {}

    for level in ['primary', 'secondary', 'tertiary']:
        if level in raw_result and isinstance(raw_result[level], list) and len(raw_result[level]) > 0:
            # Get the prediction with highest confidence for this level
            top_prediction = max(raw_result[level], key=lambda x: x.get('confidence', 0))

            transformed_result[level] = {
                "pred": top_prediction.get('label', ''),
                "confidence": top_prediction.get('confidence', 0.0),
                "reasoning": f"AI model prediction (confidence: {top_prediction.get('confidence', 0.0):.2%})",
                "key_evidence": top_prediction.get('key_evidence', {}),
                # Include primary/secondary context for child levels
                "primary": top_prediction.get('primary'),
                "secondary": top_prediction.get('secondary'),
            }

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
