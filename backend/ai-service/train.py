# train.py

from pathlib import Path
from typing import Tuple, Dict, List, Any
import re
import math

import joblib
import numpy as np
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import SGDClassifier
from sklearn.metrics import accuracy_score, f1_score

# =============================== INFERENCE CONFIG ==============================
# Global threshold for including labels per layer at inference time.
# For each layer, include ALL labels with confidence >= THRESHOLD.
# If none pass, include the single top-1 label for that layer.
THRESHOLD: float = 0.30

# =============================== HIERARCHY (enforced) ==========================
# TODO: replace with a call to your tags table; keep the same structure
HIERARCHY = {
    "primary": {
        "Disclosure": {
            "Annual_Reports": [],
            "Financial_Statements": [],
            "SEC_Filings": ["10-K", "10-Q", "S-1"],
            "Transcripts": ["AGM Transcripts", "Conference Transcripts", "Earnings Call Transcripts"],
            "Tearsheet": []
        },
        "News": {
            "Company": ["Management_Change", "Product_Launch"],
            "Industry": ["Energy", "Healthcare", "Information_Technology", "Real_Estate", "Regulation", "Supply_Chain"],
            "Macroeconomic": ["Employment", "Geopolitics", "Interest_Rates"]
        },
        "Recommendations": {
            "Analyst_Recommendations": ["Buy", "Hold", "Sell"],
            "Strategic_Recommendations": ["M&A Rationale", "Product Strategy"]
        }
    }
}

# Build allowed sets/maps
ALLOWED_PRIMARY = set(HIERARCHY["primary"].keys())
ALLOWED_SECONDARY: Dict[str, set] = {
    p: set(sec_dict.keys()) for p, sec_dict in HIERARCHY["primary"].items()
}
ALLOWED_TERTIARY: Dict[Tuple[str, str], set] = {}
for p, sec_dict in HIERARCHY["primary"].items():
    for s, ter_list in sec_dict.items():
        ALLOWED_TERTIARY[(p, s)] = set(ter_list or [])

# =============================== Pipeline =====================================
def make_pipeline():
    return Pipeline([
        ("tfidf", TfidfVectorizer(strip_accents="unicode", lowercase=True, stop_words="english")),
        ("clf", SGDClassifier(loss="hinge", random_state=42))
    ])

def _train_simple(X_train, y_train, desc: str):
    pipe = make_pipeline()
    print(f"\nTraining (no CV) on {desc} ...")
    pipe.fit(X_train, y_train)
    return None, pipe, None

def _evaluate_and_report(model, X_test, y_test, title: str):
    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    f1_macro = f1_score(y_test, y_pred, average="macro")
    f1_weighted = f1_score(y_test, y_pred, average="weighted")
    print(f"[{title}] Test Accuracy: {acc:.4f} | F1 macro: {f1_macro:.4f} | F1 weighted: {f1_weighted:.4f}")
    return {"accuracy": acc, "f1_macro": f1_macro, "f1_weighted": f1_weighted}

# =============================== Load + Enforce Hierarchy ======================
df = pd.read_csv("./training_data_text.csv")
df = df.dropna(subset=["text"]).reset_index(drop=True)

assert {"text", "primary", "secondary", "tertiary"}.issubset(df.columns), \
    "df must have columns: text, primary, secondary, tertiary"

# Primary filter
df_primary = df[df["primary"].isin(ALLOWED_PRIMARY)].copy()

# Secondary filter
def _is_allowed_secondary(row) -> bool:
    p, s = row["primary"], row["secondary"]
    return p in ALLOWED_SECONDARY and s in ALLOWED_SECONDARY.get(p, set())

df_secondary = df_primary[df_primary.apply(_is_allowed_secondary, axis=1)].copy()

# Tertiary filter — only keep rows for (p,s) that define a non-empty tertiary set and contain valid tertiary
def _is_allowed_tertiary(row) -> bool:
    p, s, t = row["primary"], row["secondary"], row["tertiary"]
    allowed_set = ALLOWED_TERTIARY.get((p, s), set())
    return len(allowed_set) > 0 and t in allowed_set

df_tertiary = df_secondary[df_secondary.apply(_is_allowed_tertiary, axis=1)].copy()

# Visibility
print("\n=== HIERARCHY ENFORCEMENT SUMMARY ===")
print(f"Rows total:              {len(df)}")
print(f"Rows after PRIMARY filt: {len(df_primary)}")
print(f"Rows after SECONDARY:    {len(df_secondary)}")
print(f"Rows after TERTIARY:     {len(df_tertiary)}")

# =============================== TRAINING ======================================
models_dir = Path("models_hier")
models_dir.mkdir(exist_ok=True)

results_hier = {"primary": {}, "secondary": {}, "tertiary": {}}

# ---------------- PRIMARY ----------------
if df_primary["primary"].nunique() >= 2:
    X = df_primary["text"].values
    y = df_primary["primary"].values
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    _, best_pipe_primary, _ = _train_simple(Xtr, ytr, "primary")
    results_hier["primary"] = _evaluate_and_report(best_pipe_primary, Xte, yte, "PRIMARY")
    joblib.dump(best_pipe_primary, models_dir / "primary.joblib")
    print(f"Saved PRIMARY model → {(models_dir / 'primary.joblib').resolve()}")
else:
    unique_p = list(df_primary["primary"].unique())
    print(f"[WARN] PRIMARY has <2 classes ({unique_p}). Skipping primary model.")
    best_pipe_primary = None

# ---------------- SECONDARY (per primary) ----------------
for p in sorted(ALLOWED_PRIMARY):
    if p not in df_secondary["primary"].unique():
        print(f"[INFO] No data for primary='{p}' at SECONDARY level. Skipping.")
        continue

    sub = df_secondary[df_secondary["primary"] == p].copy()
    if sub["secondary"].nunique() < 2:
        print(f"[WARN] SECONDARY for primary='{p}' has <2 classes. Skipping.")
        continue

    Xp_tr, Xp_te, yp_tr, yp_te = train_test_split(
        sub["text"].values, sub["secondary"].values,
        test_size=0.2, random_state=42, stratify=sub["secondary"]
    )
    _, best_pipe_secondary, _ = _train_simple(Xp_tr, yp_tr, f"secondary|{p}")
    results_hier["secondary"][p] = _evaluate_and_report(best_pipe_secondary, Xp_te, yp_te, f"SECONDARY|{p}")
    out_path = models_dir / f"secondary__{p}.joblib"
    joblib.dump(best_pipe_secondary, out_path)
    print(f"Saved SECONDARY model for primary='{p}' → {out_path.resolve()}")

# ---------------- TERTIARY (per (primary, secondary)) ----------------
valid_ps_pairs = [(p, s) for (p, s), ter_set in ALLOWED_TERTIARY.items() if len(ter_set) > 0]

for p, s in sorted(valid_ps_pairs):
    sub = df_tertiary[(df_tertiary["primary"] == p) & (df_tertiary["secondary"] == s)].copy()
    if sub.empty:
        print(f"[INFO] No data for tertiary under (primary='{p}', secondary='{s}'). Skipping.")
        continue

    if sub["tertiary"].nunique() < 2:
        print(f"[WARN] TERTIARY for (primary='{p}', secondary='{s}') has <2 classes. Skipping.")
        continue

    Xt_tr, Xt_te, yt_tr, yt_te = train_test_split(
        sub["text"].values, sub["tertiary"].values,
        test_size=0.2, random_state=42, stratify=sub["tertiary"]
    )
    _, best_pipe_tertiary, _ = _train_simple(Xt_tr, yt_tr, f"tertiary|{p}|{s}")
    results_hier["tertiary"][(p, s)] = _evaluate_and_report(
        best_pipe_tertiary, Xt_te, yt_te, f"TERTIARY|{p}|{s}"
    )
    out_path = models_dir / f"tertiary__{p}__{s}.joblib"
    joblib.dump(best_pipe_tertiary, out_path)
    print(f"Saved TERTIARY model for (p='{p}', s='{s}') → {out_path.resolve()}")

# =============================== SHAP (optional) ===============================
try:
    import shap
    _HAS_SHAP = True
    try:
        shap.explainers._explainer.progress = False
    except Exception:
        pass
except Exception:
    _HAS_SHAP = False

# =============================== Inference Wrapper =============================
class HierarchicalBestModel:
    """
    Thresholded, multi-branch hierarchical inference.

    For each layer (primary, secondary, tertiary):
      - score all classes and convert to confidences via sigmoid(decision_function)
      - select all classes with confidence >= self.threshold
      - if none pass threshold, keep the single top-1
      - expand to next layer for ALL selected parents
    """
    def __init__(self, primary_model, secondary_models, tertiary_models, threshold: float = THRESHOLD):
        self.primary_model = primary_model
        self.secondary_models = secondary_models  # {primary: model}
        self.tertiary_models = tertiary_models    # {(primary, secondary): model}
        self.threshold = float(threshold)
        self._shap_cache = {}

    # ---------- scoring helpers ----------
    @staticmethod
    def _binary_scores_to_full(scores_1d: float, classes: List[str]) -> np.ndarray:
        """
        For binary OvR, sklearn's decision_function returns shape (n,)
        meaning the signed distance for the positive class (classes_[1]).
        Reconstruct two-class scores as [ -margin, +margin ] aligned to classes order.
        """
        assert len(classes) == 2
        pos_margin = float(scores_1d)
        return np.array([-pos_margin, pos_margin], dtype=float)

    @staticmethod
    def _soft_sigmoid(x: float) -> float:
        # Stable sigmoid for calibration-like confidence (monotonic with margin)
        return 1.0 / (1.0 + math.exp(-x))

    def _scores_confidences(self, model, text: str) -> List[Dict[str, Any]]:
        """
        Return [{label, score, confidence}] sorted by score desc for ALL classes.
        score = decision_function distance; confidence = sigmoid(score).
        Handles binary and multiclass consistently.
        """
        raw = model.decision_function([text])
        labels = [str(c) for c in model.classes_]

        if np.ndim(raw) == 1:  # could be binary with shape (1,) or multiclass (1, K) collapsed by sklearn
            raw = np.asarray(raw)
            if raw.shape == (1,):
                # Binary case returning margin for positive class
                scores = self._binary_scores_to_full(raw[0], labels)
            else:
                # Multiclass returns shape (K,)
                scores = raw
        else:
            # shape (1, K)
            scores = raw[0]

        # Confidences per class via sigmoid of per-class margin
        items = []
        for lab, sc in zip(labels, scores):
            items.append({
                "label": lab,
                "score": float(sc),
                "confidence": float(self._soft_sigmoid(float(sc)))
            })
        # Sort by score descending
        items.sort(key=lambda d: d["score"], reverse=True)
        return items

    # ---------- SHAP helpers ----------
    def _get_shap_explainer(self, model):
        if not _HAS_SHAP:
            return None
        key = id(model)
        if key not in self._shap_cache:
            try:
                masker = shap.maskers.Text()
                f = lambda texts: model.decision_function(texts)
                self._shap_cache[key] = shap.Explainer(f, masker, show_progress=False)
            except Exception:
                return None
        return self._shap_cache[key]

    def _shap_for_label(self, model, text: str, label: str, top_k: int = 10):
        """
        Compute token-level SHAP for a specific predicted label (multiclass: pick that class index).
        Returns {"supporting": [...], "opposing": [...]} lists.
        """
        if not _HAS_SHAP:
            return {"supporting": [], "opposing": []}

        explainer = self._get_shap_explainer(model)
        if explainer is None:
            return {"supporting": [], "opposing": []}

        sv = explainer([text])
        try:
            classes = list(model.classes_)
        except Exception:
            classes = []

        if getattr(sv.values, "ndim", 0) == 3:
            # sv.values shape: (1, n_classes, n_tokens)
            try:
                idx = classes.index(label) if label in classes else int(np.argmax(sv.base_values[0]))
            except Exception:
                idx = 0
            shap_vals = sv.values[0, idx]
            tokens = sv.data[0]
        else:
            shap_vals = sv.values[0]
            tokens = sv.data[0]

        pairs = list(zip(tokens, shap_vals))
        pairs_sorted = sorted(pairs, key=lambda x: abs(x[1]), reverse=True)[:top_k]

        supporting, opposing = [], []
        for tok, val in pairs_sorted:
            entry = {"token": tok, "impact": f"{'+' if val >= 0 else '-'}{abs(val)*100:.2f}%"}
            (supporting if val >= 0 else opposing).append(entry)

        return {"supporting": supporting, "opposing": opposing}

    # ---------- selection per layer ----------
    def _select_by_threshold(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Keep all with confidence >= threshold. If none, keep the single best (top-1).
        """
        selected = [d for d in items if d["confidence"] >= self.threshold]
        if not selected and items:
            selected = [items[0]]  # top-1 fallback
        return selected

    # ---------- public inference ----------
    def predict_one(self, text: str) -> Dict[str, Any]:
        """
        Returns:
        {
          "threshold": 0.7,
          "primary":   [ {label, confidence, key_evidence}, ... ],
          "secondary": [ {primary, label, confidence, key_evidence}, ... ],
          "tertiary":  [ {primary, secondary, label, confidence, key_evidence}, ... ]
        }
        """
        out: Dict[str, Any] = {"threshold": self.threshold, "primary": [], "secondary": [], "tertiary": []}

        # PRIMARY
        if self.primary_model is None:
            return out  # nothing trained; return empty lists

        prim_scores = self._scores_confidences(self.primary_model, text)
        prim_selected = self._select_by_threshold(prim_scores)

        # attach SHAP for each selected primary
        primary_results = []
        for item in prim_selected:
            ev = self._shap_for_label(self.primary_model, text, item["label"])
            primary_results.append({
                "label": item["label"],
                "confidence": item["confidence"],
                "key_evidence": ev
            })
        out["primary"] = primary_results

        # SECONDARY (for each selected primary)
        secondary_results = []
        for p_item in primary_results:
            p_label = p_item["label"]
            s_model = self.secondary_models.get(p_label)
            if not s_model:
                continue

            sec_scores = self._scores_confidences(s_model, text)
            sec_selected = self._select_by_threshold(sec_scores)

            for s_item in sec_selected:
                ev = self._shap_for_label(s_model, text, s_item["label"])
                secondary_results.append({
                    "primary": p_label,
                    "label": s_item["label"],
                    "confidence": s_item["confidence"],
                    "key_evidence": ev
                })
        out["secondary"] = secondary_results

        # TERTIARY (for each selected (primary, secondary))
        tertiary_results = []
        for s_item in secondary_results:
            p_label = s_item["primary"]
            s_label = s_item["label"]
            t_model = self.tertiary_models.get((p_label, s_label))
            if not t_model:
                continue

            ter_scores = self._scores_confidences(t_model, text)
            ter_selected = self._select_by_threshold(ter_scores)

            for t_item in ter_selected:
                ev = self._shap_for_label(t_model, text, t_item["label"])
                tertiary_results.append({
                    "primary": p_label,
                    "secondary": s_label,
                    "label": t_item["label"],
                    "confidence": t_item["confidence"],
                    "key_evidence": ev
                })
        out["tertiary"] = tertiary_results

        return out

    def predict(self, texts: List[str]) -> List[Dict[str, Any]]:
        return [self.predict_one(t) for t in texts]

# =============================== Builder =======================================
def build_best_model(models_dir: Path) -> HierarchicalBestModel:
    primary_path = models_dir / "primary.joblib"
    primary_model = joblib.load(primary_path) if primary_path.exists() else None

    secondary_models, tertiary_models = {}, {}

    for pth in models_dir.glob("secondary__*.joblib"):
        p = pth.stem[len("secondary__"):]
        if p in ALLOWED_PRIMARY:
            secondary_models[p] = joblib.load(pth)

    for pth in models_dir.glob("tertiary__*__*.joblib"):
        m = re.match(r"tertiary__(.+)__(.+)$", pth.stem)
        if m:
            p, s = m.groups()
            if (p in ALLOWED_PRIMARY) and (s in ALLOWED_SECONDARY.get(p, set())) and len(ALLOWED_TERTIARY.get((p, s), set())) > 0:
                tertiary_models[(p, s)] = joblib.load(pth)

    # Pass the threshold into the wrapper so it’s serialized with the model
    return HierarchicalBestModel(primary_model, secondary_models, tertiary_models, threshold=THRESHOLD)

# =============================== Persist wrapper ===============================
best_model = build_best_model(models_dir)
joblib.dump(best_model, models_dir / "best_model.joblib")
print(f"Saved hierarchical wrapper → {(models_dir / 'best_model.joblib').resolve()}")
