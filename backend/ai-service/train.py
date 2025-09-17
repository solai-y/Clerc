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

# =============================== HIERARCHY (enforced) ==========================
# to be replaced with a call to the tags table to obtain heirarchy -- but should be made into this format
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

# build allowed sets/maps to know which are not allows and allowed
ALLOWED_PRIMARY = set(HIERARCHY["primary"].keys())
ALLOWED_SECONDARY: Dict[str, set] = {
    p: set(sec_dict.keys()) for p, sec_dict in HIERARCHY["primary"].items()
}
ALLOWED_TERTIARY: Dict[Tuple[str, str], set] = {}
for p, sec_dict in HIERARCHY["primary"].items():
    for s, ter_list in sec_dict.items():
        # Note: ter_list may be [], meaning: no tertiary level under (p,s)
        ALLOWED_TERTIARY[(p, s)] = set(ter_list or [])

# =============================== Pipeline ==========================
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

# check strucutre of CSV
assert {"text", "primary", "secondary", "tertiary"}.issubset(df.columns), \
    "df must have columns: text, primary, secondary, tertiary"

# this check is to cover the situation where the primary tag is deleted, it will allow the model to ignore those documents
df_primary = df[df["primary"].isin(ALLOWED_PRIMARY)].copy()

# check if secondary layer tag exists
def _is_allowed_secondary(row) -> bool:
    p, s = row["primary"], row["secondary"]
    return p in ALLOWED_SECONDARY and s in ALLOWED_SECONDARY.get(p, set())

df_secondary = df_primary[df_primary.apply(_is_allowed_secondary, axis=1)].copy()

# check if teritiary layer tags exists and if they have at least 1 document at that node
def _is_allowed_tertiary(row) -> bool:
    p, s, t = row["primary"], row["secondary"], row["tertiary"]
    allowed_set = ALLOWED_TERTIARY.get((p, s), set())
    # If allowed_set is empty, this (p,s) has no tertiary level → skip entirely.
    return len(allowed_set) > 0 and t in allowed_set

df_tertiary = df_secondary[df_secondary.apply(_is_allowed_tertiary, axis=1)].copy()

# Basic visibility into what we kept
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
    # Either 0 or 1 class → skip training
    unique_p = list(df_primary["primary"].unique())
    print(f"[WARN] PRIMARY has <2 classes ({unique_p}). Skipping primary model.")
    best_pipe_primary = None

# ---------------- SECONDARY (per primary) ----------------
for p in sorted(ALLOWED_PRIMARY):
    # Only consider (existing in data) secondaries under p
    if p not in df_secondary["primary"].unique():
        print(f"[INFO] No data for primary='{p}' at SECONDARY level. Skipping.")
        continue

    sub = df_secondary[df_secondary["primary"] == p].copy()
    # Keep only secondary labels that appear at least once (implicit by sub) and with >=2 classes overall
    if sub["secondary"].nunique() < 2:
        print(f"[WARN] SECONDARY for primary='{p}' has <2 classes. Skipping.")
        continue

    # Train
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
# Only train tertiary for (p,s) where hierarchy defines a NON-EMPTY tertiary list
valid_ps_pairs = [(p, s) for (p, s), ter_set in ALLOWED_TERTIARY.items() if len(ter_set) > 0]

for p, s in sorted(valid_ps_pairs):
    # Check data exists for this (p,s)
    sub = df_tertiary[(df_tertiary["primary"] == p) & (df_tertiary["secondary"] == s)].copy()
    if sub.empty:
        print(f"[INFO] No data for tertiary under (primary='{p}', secondary='{s}'). Skipping.")
        continue

    # Need at least 2 tertiary classes to train a classifier
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

# ===================== BEST MODEL (with SHAP key_evidence) ==================
# SHAP for explanations
try:
    import shap
    _HAS_SHAP = True
    # Silence SHAP tqdm noise if any
    try:
        shap.explainers._explainer.progress = False
    except Exception:
        pass
except Exception:
    _HAS_SHAP = False

class HierarchicalBestModel:
    def __init__(self, primary_model, secondary_models, tertiary_models):
        self.primary_model = primary_model
        self.secondary_models = secondary_models
        self.tertiary_models = tertiary_models
        self._shap_cache = {}

    @staticmethod
    def _score_and_confidence(model, text: str) -> Dict[str, Any]:
        scores = model.decision_function([text])[0]
        labels = [str(c) for c in model.classes_]
        if np.ndim(scores) == 0:  # binary
            pred = labels[1] if scores >= 0 else labels[0]
            margin = abs(float(scores))
        else:
            order = np.argsort(scores)[::-1]
            pred = labels[order[0]]
            margin = scores[order[0]] - scores[order[1]] if len(scores) > 1 else scores[order[0]]
        confidence = 1 / (1 + math.exp(-margin))
        return {"pred": pred, "confidence": float(confidence)}

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

    def _shap_explain_text(self, model, text: str, pred_label: str, top_k: int = 10):
        if not _HAS_SHAP:
            return {"key_evidence": {"supporting": [], "opposing": []}}
        explainer = self._get_shap_explainer(model)
        if explainer is None:
            return {"key_evidence": {"supporting": [], "opposing": []}}

        sv = explainer([text])
        if getattr(sv.values, "ndim", 0) == 3:  # multiclass
            classes = list(model.classes_)
            idx = classes.index(pred_label) if pred_label in classes else int(np.argmax(sv.base_values[0]))
            shap_vals = sv.values[0, idx]
            tokens = sv.data[0]
        else:
            shap_vals = sv.values[0]
            tokens = sv.data[0]

        pairs = list(zip(tokens, shap_vals))
        pairs_sorted = sorted(pairs, key=lambda x: abs(x[1]), reverse=True)[:top_k]

        supporting, opposing = [], []
        for tok, val in pairs_sorted:
            impact = f"{'+' if val >= 0 else '-'}{abs(val)*100:.2f}%"
            entry = {"token": tok, "impact": impact}
            if val >= 0:
                supporting.append(entry)
            else:
                opposing.append(entry)

        return {"key_evidence": {"supporting": supporting, "opposing": opposing}}

    def predict_one(self, text: str) -> Dict[str, Any]:
        out: Dict[str, Any] = {}

        # PRIMARY (only if model exists)
        if self.primary_model is None:
            out["primary"] = {"pred": None, "confidence": None, "key_evidence": {"supporting": [], "opposing": []}}
            return out

        p_res = self._score_and_confidence(self.primary_model, text)
        p_shap = self._shap_explain_text(self.primary_model, text, p_res["pred"])
        out["primary"] = {**p_res, **p_shap}

        # SECONDARY (conditioned on predicted primary)
        s_model = self.secondary_models.get(p_res["pred"])
        if s_model:
            s_res = self._score_and_confidence(s_model, text)
            s_shap = self._shap_explain_text(s_model, text, s_res["pred"])
            out["secondary"] = {**s_res, "primary": p_res["pred"], **s_shap}
        else:
            out["secondary"] = {"pred": None, "confidence": None, "primary": p_res["pred"],
                                "key_evidence": {"supporting": [], "opposing": []}}

        # TERTIARY (conditioned on predicted (primary, secondary))
        s_pred = out["secondary"]["pred"]
        if s_pred:
            t_model = self.tertiary_models.get((p_res["pred"], s_pred))
            if t_model:
                t_res = self._score_and_confidence(t_model, text)
                t_shap = self._shap_explain_text(t_model, text, t_res["pred"])
                out["tertiary"] = {**t_res, "primary": p_res["pred"], "secondary": s_pred, **t_shap}
            else:
                out["tertiary"] = {"pred": None, "confidence": None, "primary": p_res["pred"], "secondary": s_pred,
                                   "key_evidence": {"supporting": [], "opposing": []}}
        else:
            out["tertiary"] = {"pred": None, "confidence": None, "primary": p_res["pred"], "secondary": None,
                               "key_evidence": {"supporting": [], "opposing": []}}
        return out

    def predict(self, texts: List[str]) -> List[Dict[str, Any]]:
        return [self.predict_one(t) for t in texts]

def build_best_model(models_dir: Path) -> HierarchicalBestModel:
    primary_path = models_dir / "primary.joblib"
    primary_model = joblib.load(primary_path) if primary_path.exists() else None

    secondary_models, tertiary_models = {}, {}

    # Only load secondary models for PRIMARY labels that exist in hierarchy (defensive)
    for pth in models_dir.glob("secondary__*.joblib"):
        p = pth.stem[len("secondary__"):]
        if p in ALLOWED_PRIMARY:
            secondary_models[p] = joblib.load(pth)

    # Only load tertiary models for valid (p,s) pairs that have non-empty tertiary lists
    for pth in models_dir.glob("tertiary__*__*.joblib"):
        m = re.match(r"tertiary__(.+)__(.+)$", pth.stem)
        if m:
            p, s = m.groups()
            if (p in ALLOWED_PRIMARY) and (s in ALLOWED_SECONDARY.get(p, set())) and len(ALLOWED_TERTIARY.get((p, s), set())) > 0:
                tertiary_models[(p, s)] = joblib.load(pth)

    return HierarchicalBestModel(primary_model, secondary_models, tertiary_models)

# Build wrapper and persist
best_model = build_best_model(models_dir)
joblib.dump(best_model, models_dir / "best_model.joblib")
print(f"Saved hierarchical wrapper → {(models_dir / 'best_model.joblib').resolve()}")
