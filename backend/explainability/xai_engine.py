import re
from typing import Dict, List, Any, Tuple
import numpy as np

class XAIEngine:
    def __init__(self, vectorizer=None, model=None):
        self.vectorizer = vectorizer
        self.model = model

    def set_model_and_vectorizer(self, model, vectorizer):
        self.model = model
        self.vectorizer = vectorizer

    def explain_instance(self, preprocessed_text: str, top_k: int = 10) -> Dict[str, Any]:
        """Calculates token-level feature importance and term weights for a given input."""
        if not self.vectorizer or not self.model:
            return {"fake_indicators": [], "real_indicators": [], "top_features": []}

        # Transform single instance
        tfidf_vec = self.vectorizer.transform([preprocessed_text])
        feature_names = np.array(self.vectorizer.get_feature_names_out())
        
        # Non-zero indices in current text
        cx = tfidf_vec.tocoo()
        doc_indices = cx.col
        doc_values = cx.data

        if len(doc_indices) == 0:
            return {"fake_indicators": [], "real_indicators": [], "top_features": []}

        # Extract weights based on model type
        weights = np.zeros(len(doc_indices))

        if hasattr(self.model, "coef_"):
            # Linear model (Logistic Regression, LinearSVC)
            coefs = self.model.coef_[0]
            for i, (idx, val) in enumerate(zip(doc_indices, doc_values)):
                weights[i] = coefs[idx] * val
        elif hasattr(self.model, "feature_importances_"):
            # Tree-based model (Random Forest, XGBoost)
            importances = self.model.feature_importances_
            # Tree importances are non-negative, so we assign directional sign based on prediction
            pred_class = self.model.predict(tfidf_vec)[0]
            sign = 1.0 if pred_class == 1 else -1.0
            for i, (idx, val) in enumerate(zip(doc_indices, doc_values)):
                weights[i] = importances[idx] * val * sign
        elif hasattr(self.model, "feature_log_prob_"):
            # Naive Bayes (log probability difference between classes)
            diff = self.model.feature_log_prob_[1] - self.model.feature_log_prob_[0]
            for i, (idx, val) in enumerate(zip(doc_indices, doc_values)):
                weights[i] = diff[idx] * val
        elif hasattr(self.model, "calibrated_classifiers_"):
            # CalibratedClassifierCV wrapper
            sub_weights = []
            for cal_clf in self.model.calibrated_classifiers_:
                base = cal_clf.estimator
                if hasattr(base, "coef_"):
                    sub_weights.append(base.coef_[0])
            if sub_weights:
                avg_coef = np.mean(sub_weights, axis=0)
                for i, (idx, val) in enumerate(zip(doc_indices, doc_values)):
                    weights[i] = avg_coef[idx] * val
            else:
                weights = doc_values

        doc_features = feature_names[doc_indices]
        
        # Separate into fake (positive weight) and real (negative weight) indicators
        term_score_pairs = list(zip(doc_features, weights, doc_values))
        
        # Sort by absolute weight magnitude
        sorted_pairs = sorted(term_score_pairs, key=lambda x: abs(x[1]), reverse=True)

        fake_indicators = []
        real_indicators = []

        for term, weight, tfidf_val in sorted_pairs:
            item = {
                "term": term,
                "weight": round(float(weight), 4),
                "tfidf_value": round(float(tfidf_val), 4),
                "impact": "Misleading Signal" if weight > 0 else "Credibility Signal"
            }
            if weight > 0:
                fake_indicators.append(item)
            else:
                real_indicators.append(item)

        top_features = sorted_pairs[:top_k]
        formatted_top = [
            {
                "term": term,
                "weight": round(float(weight), 4),
                "direction": "MISLEADING" if weight > 0 else "CREDIBLE",
                "magnitude": round(abs(float(weight)), 4)
            }
            for term, weight, _ in top_features
        ]

        return {
            "top_features": formatted_top,
            "fake_indicators": fake_indicators[:top_k],
            "real_indicators": real_indicators[:top_k],
            "total_active_features": len(doc_indices)
        }

xai_engine = XAIEngine()
