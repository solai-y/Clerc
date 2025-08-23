from __future__ import annotations
import os, joblib, numpy as np
from typing import List, Tuple, Dict, Any

class HierarchicalTagger:
    def __init__(self, bundle_path: str):
        self.bundle_path = bundle_path
        self.bundle: Dict[str, Any] | None = None
        self.vec = None
        self.clf1 = None
        self.c1 = None
        self.l2 = {}
        self.l3 = {}

    def load(self):
        if not os.path.exists(self.bundle_path):
            raise FileNotFoundError(self.bundle_path)
        self.bundle = joblib.load(self.bundle_path)
        self.vec = self.bundle["vectorizer"]
        self.clf1 = self.bundle["l1"]; self.c1 = self.bundle["l1_classes"]
        self.l2 = self.bundle["l2"];   self.l3 = self.bundle["l3"]
        return self

    @staticmethod
    def _proba(clf, X):
        if hasattr(clf, "predict_proba"): return clf.predict_proba(X)
        scores = clf.decision_function(X)
        if scores.ndim == 1: scores = scores.reshape(-1, 1)
        exp = np.exp(scores - scores.max(axis=1, keepdims=True))
        return exp / exp.sum(axis=1, keepdims=True)

    def predict_all(self, texts: List[str], beam1: int = 3, beam2: int = 3, beam3: int = 3) -> List[List[Tuple[str, float]]]:
        X = self.vec.transform(texts)
        out: List[List[Tuple[str, float]]] = []
        for i in range(X.shape[0]):
            Xi = X[i]
            p1 = self._proba(self.clf1, Xi)
            l1_idx_sorted = np.argsort(p1[0])[::-1][:beam1]
            candidates: List[Tuple[str, float]] = []
            for a in l1_idx_sorted:
                l1_name = str(self.c1[a]); p1a = float(p1[0, a])
                if l1_name in self.l2:
                    clf2 = self.l2[l1_name]["clf"]; c2 = self.l2[l1_name]["classes"]
                    p2 = self._proba(clf2, Xi)
                    l2_idx_sorted = np.argsort(p2[0])[::-1][:beam2]
                    for b in l2_idx_sorted:
                        l2_name = str(c2[b]); p1a2b = p1a * float(p2[0, b])
                        key = (l1_name, l2_name)
                        if key in self.l3:
                            clf3 = self.l3[key]["clf"]; c3 = self.l3[key]["classes"]
                            p3 = self._proba(clf3, Xi)
                            l3_idx_sorted = np.argsort(p3[0])[::-1][:beam3]
                            for c in l3_idx_sorted:
                                leaf = str(c3[c]); prob = p1a2b * float(p3[0, c])
                                candidates.append((leaf, prob))
                        else:
                            candidates.append((l2_name, p1a2b))
                else:
                    candidates.append((l1_name, p1a))
            candidates.sort(key=lambda x: x[1], reverse=True)
            out.append(candidates)
        return out

    def predict_top(self, texts: List[str], top_k: int = 5) -> List[List[Tuple[str, float]]]:
        all_preds = self.predict_all(texts)
        return [preds[:top_k] for preds in all_preds]

def load_tagger(bundle_path: str):
    return HierarchicalTagger(bundle_path).load()
