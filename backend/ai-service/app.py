from __future__ import annotations
import io, os, json, hashlib, traceback
from datetime import datetime, timezone
from typing import Dict, List, Tuple
from flask import Flask, request, jsonify
from flask_cors import CORS
import fitz
from shared.model import load_tagger

BUNDLE_PATH = os.getenv("HIER_BUNDLE_PATH", "/models/hier_bundle.joblib")
HIER_PATH   = os.getenv("HIER_PATH", "/app/shared/tag_hierarchy.json")
ENABLE_OCR  = os.getenv("ENABLE_OCR", "1") == "1"
MAX_MB      = int(os.getenv("MAX_UPLOAD_MB", "50"))

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = MAX_MB * 1024 * 1024
CORS(app, resources={r"/ai/*": {"origins": "*"}})

_tagger = None
_child_to_group: Dict[str, str] | None = None
_model_meta: Dict[str, str] | None = None

def _ensure_model():
    global _tagger, _model_meta
    if _tagger is None:
        _tagger = load_tagger(BUNDLE_PATH)
        try:
            st = os.stat(BUNDLE_PATH)
            _model_meta = {
                "model_updated_at": datetime.fromtimestamp(st.st_mtime, tz=timezone.utc).isoformat(),
                "model_hash": _sha256_file(BUNDLE_PATH)
            }
        except Exception:
            _model_meta = None

def _ensure_hierarchy():
    global _child_to_group
    if _child_to_group is not None:
        return
    _child_to_group = {}
    try:
        with open(HIER_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        def walk(node, path):
            if isinstance(node, dict):
                for k, v in node.items():
                    walk(v, path + [k])
            elif isinstance(node, list):
                group = ">".join(path) if path else "__root__"
                for leaf in node:
                    _child_to_group[str(leaf)] = group
            else:
                _child_to_group[str(node)] = ">".join(path) if path else "__root__"
        walk(data, [])
    except FileNotFoundError:
        _child_to_group = {}
    except Exception as e:
        app.logger.warning("Failed to load hierarchy: %s", e)
        _child_to_group = {}

def _apply_sibling_exclusion(ranked: List[Tuple[str,float]], k: int) -> List[Tuple[str,float]]:
    _ensure_hierarchy()
    groups = set(); out = []
    for tag, score in ranked:
        group = _child_to_group.get(tag, tag)
        if group in groups: continue
        out.append((tag, float(score))); groups.add(group)
        if len(out) >= k: break
    return out

def _extract_text(b: bytes) -> str:
    doc = fitz.open(stream=io.BytesIO(b), filetype="pdf")
    chunks = []
    for p in doc:
        txt = (p.get_text() or "").strip()
        if not txt and ENABLE_OCR:
            try: txt = (p.get_text("ocr") or "").strip()
            except Exception: pass
        chunks.append(txt)
    return "\n".join(chunks)

def _sha256_file(path: str) -> str:
    import hashlib
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1<<20), b""):
            h.update(chunk)
    return h.hexdigest()[:16]

@app.get("/ai/v1/health")
def health():
    if not os.path.exists(BUNDLE_PATH):
        return jsonify({"status":"missing_bundle","bundle_path":BUNDLE_PATH,"uses_hier":True})
    try:
        _ensure_model(); _ensure_hierarchy()
        return jsonify({"status":"ok","uses_hier":True,"hier_loaded":bool(_child_to_group),
                        "bundle_path":BUNDLE_PATH, **(_model_meta or {})})
    except Exception as e:
        return jsonify({"status":"error_loading","error":str(e)}), 500

@app.get("/ai/v1/version")
def version():
    _ensure_model()
    return jsonify(_model_meta or {"model":"unknown"})

@app.post("/ai/v1/predict")
def predict():
    try:
        if request.content_length and request.content_length > app.config["MAX_CONTENT_LENGTH"]:
            return jsonify({"error":"File too large"}), 413
        if "pdf" not in request.files:
            return jsonify({"error":"No file uploaded under field 'pdf'"}), 400
        f = request.files["pdf"]
        if "pdf" not in (f.mimetype or "").lower():
            return jsonify({"error":f"Unsupported content type: {f.mimetype}"}), 415

        _ensure_model(); _ensure_hierarchy()
        text = _extract_text(f.read())
        k = int(request.args.get("top_k", 5))
        ranked = _tagger.predict_all([text])[0]
        filtered = _apply_sibling_exclusion(ranked, k)
        return jsonify({"filename": f.filename, "tags": [{"tag": t, "score": float(s)} for t, s in filtered]})
    except Exception as e:
        app.logger.exception("predict failed")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
