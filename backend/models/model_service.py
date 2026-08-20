import json
import joblib
from pathlib import Path
from typing import Dict, Any, List, Optional
import numpy as np

from backend.config import SAVED_MODELS_DIR, settings
from backend.nlp.preprocessor import preprocessor
from backend.nlp.feature_extractor import FeatureExtractor
from backend.nlp.linguistic_analyzer import linguistic_analyzer
from backend.explainability.xai_engine import xai_engine
from backend.explainability.highlighter import highlighter

class ModelService:
    def __init__(self):
        self.vectorizer = FeatureExtractor()
        self.models: Dict[str, Any] = {}
        self.metrics: Dict[str, Any] = {}
        self.active_model_key: str = settings.DEFAULT_MODEL
        self.is_loaded = False
        self.load_artifacts()

    def load_artifacts(self):
        """Loads saved models, vectorizer, and benchmark metrics."""
        vec_path = SAVED_MODELS_DIR / "tfidf_vectorizer.joblib"
        if vec_path.exists():
            self.vectorizer.load(vec_path)

        model_keys = ["linear_svm", "xgboost", "logistic_regression", "naive_bayes", "random_forest"]
        for key in model_keys:
            model_path = SAVED_MODELS_DIR / f"{key}.joblib"
            if model_path.exists():
                self.models[key] = joblib.load(model_path)

        metrics_path = SAVED_MODELS_DIR / "metrics.json"
        if metrics_path.exists():
            with open(metrics_path, "r") as f:
                self.metrics = json.load(f)

        if self.active_model_key not in self.models and self.models:
            self.active_model_key = list(self.models.keys())[0]

        self.is_loaded = True
        print(f"[ModelService] Loaded {len(self.models)} models. Active: {self.active_model_key}")

    def set_active_model(self, model_key: str) -> bool:
        """Dynamically switches the active production classifier."""
        if model_key in self.models:
            self.active_model_key = model_key
            return True
        return False

    def predict_with_model(self, model_key: str, X_vec) -> Dict[str, Any]:
        """Runs inference for a specific model key."""
        model = self.models.get(model_key)
        if not model:
            return {"label": 0, "prob_fake": 0.5, "confidence": 50.0}

        pred = int(model.predict(X_vec)[0])
        if hasattr(model, "predict_proba"):
            probs = model.predict_proba(X_vec)[0]
            prob_fake = float(probs[1])
            prob_real = float(probs[0])
        elif hasattr(model, "decision_function"):
            df = float(model.decision_function(X_vec)[0])
            prob_fake = 1.0 / (1.0 + np.exp(-df))
            prob_real = 1.0 - prob_fake
        else:
            prob_fake = 1.0 if pred == 1 else 0.0
            prob_real = 1.0 - prob_fake

        confidence = max(prob_fake, prob_real) * 100.0

        return {
            "prediction_class": pred, # 0 = Real, 1 = Fake
            "prob_fake": round(prob_fake, 4),
            "prob_real": round(prob_real, 4),
            "confidence": round(confidence, 1)
        }

    def determine_verdict(self, risk_score: float, model_confidence: float, word_count: int, prob_fake: float) -> Dict[str, Any]:
        """
        Maps probability and risk score to the 4-tier verdict system:
        - REAL / LOW RISK
        - SUSPICIOUS / REVIEW
        - LIKELY MISLEADING
        - INSUFFICIENT EVIDENCE
        """
        if word_count < settings.MIN_TEXT_LENGTH:
            return {
                "verdict": "INSUFFICIENT EVIDENCE",
                "badge_color": "gray",
                "summary": "Text content is too brief for a statistically reliable assessment. Please provide the full article."
            }

        # 4-tier logic
        if risk_score >= settings.RISK_THRESHOLD_HIGH or prob_fake >= 0.70:
            return {
                "verdict": "LIKELY MISLEADING",
                "badge_color": "red",
                "summary": "The content strongly matches linguistic patterns, stylistic indicators, and rhetorical structures associated with misleading or fabricated news in trained models."
            }
        elif risk_score >= settings.RISK_THRESHOLD_LOW or (0.35 <= prob_fake <= 0.69):
            return {
                "verdict": "SUSPICIOUS / REVIEW",
                "badge_color": "amber",
                "summary": "The content contains mixed signals, sensational hooks, or ambiguous framing that warrants secondary verification against authoritative sources."
            }
        else:
            return {
                "verdict": "REAL / LOW RISK",
                "badge_color": "emerald",
                "summary": "The content exhibits standard journalistic attribution, neutral phrasing, and statistical characteristics consistent with reliable reporting."
            }

    def analyze(self, headline: str = "", content: str = "", model_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Comprehensive analysis pipeline:
        1. NLP Preprocessing & Statistics
        2. Feature Vectorization
        3. Multi-Model Inference (Active + Comparison across all 5)
        4. Explainable AI (XAI) Token Attribution
        5. Linguistic Risk Indicators
        6. Span Highlighting
        7. Verdict & Confidence Synthesis
        """
        combined_text = f"{headline}. {content}".strip() if headline else content.strip()
        stats = preprocessor.extract_stats(combined_text)
        
        # Selected model
        chosen_model_key = model_name if (model_name and model_name in self.models) else self.active_model_key
        active_model = self.models.get(chosen_model_key)

        # NLP Clean & Preprocess
        preprocessed = preprocessor.preprocess(combined_text)
        
        # Transform into TF-IDF vector
        X_vec = self.vectorizer.transform([preprocessed])

        # Active model prediction
        active_pred = self.predict_with_model(chosen_model_key, X_vec)

        # Multi-model comparative results across all 5 classifiers
        comparison_results = {}
        for key in self.models.keys():
            res = self.predict_with_model(key, X_vec)
            meta = self.metrics.get("models", {}).get(key, {})
            comparison_results[key] = {
                "model_name": meta.get("name", key),
                "model_type": meta.get("type", "Classifier"),
                "prediction": "MISLEADING" if res["prediction_class"] == 1 else "CREDIBLE",
                "prob_fake": res["prob_fake"],
                "prob_real": res["prob_real"],
                "confidence": res["confidence"],
                "f1_score": meta.get("f1_score", 0.0)
            }

        # Explainable AI (XAI) calculations
        xai_engine.set_model_and_vectorizer(active_model, self.vectorizer.vectorizer)
        xai_explanation = xai_engine.explain_instance(preprocessed, top_k=10)

        # Linguistic Risk Profile
        risk_profile = linguistic_analyzer.compute_composite_risk_score(
            text=content or headline,
            headline=headline,
            model_prob_fake=active_pred["prob_fake"]
        )

        # In-text Annotation & Highlighting
        highlight_data = highlighter.annotate_spans(
            raw_text=combined_text,
            top_xai_terms=xai_explanation.get("top_features", [])
        )

        # 4-Tier Verdict Calculation
        verdict_data = self.determine_verdict(
            risk_score=risk_profile["composite_risk_score"],
            model_confidence=active_pred["confidence"],
            word_count=stats["word_count"],
            prob_fake=active_pred["prob_fake"]
        )

        # Explainable bullet-point rationale
        explanation_bullets = []
        if risk_profile["breakdown"]["sensationalism"]["severity"] in ["HIGH", "MEDIUM"]:
            count = risk_profile["breakdown"]["sensationalism"]["term_count"]
            explanation_bullets.append(f"Detected {count} sensational/hyperbolic phrases (e.g. {', '.join([t['term'] for t in risk_profile['breakdown']['sensationalism']['matched_terms'][:3]])}).")
        
        if risk_profile["breakdown"]["clickbait"]["severity"] in ["HIGH", "MEDIUM"]:
            explanation_bullets.append(f"Identified curiosity-gap clickbait phrasing designed to trigger emotional response.")
        
        if risk_profile["breakdown"]["emotional_intensity"]["severity"] in ["HIGH", "MEDIUM"]:
            subj = risk_profile["breakdown"]["emotional_intensity"]["subjectivity"]
            explanation_bullets.append(f"High subjective valence (Subjectivity index: {subj}), deviating from neutral journalistic standards.")
            
        if risk_profile["breakdown"]["punctuation_caps"]["severity"] in ["HIGH", "MEDIUM"]:
            caps = risk_profile["breakdown"]["punctuation_caps"]["caps_word_count"]
            explanation_bullets.append(f"Excessive formatting anomalies detected ({caps} uppercase shouting words or repeated exclamation/question marks).")
            
        if risk_profile["breakdown"]["headline_mismatch"]["mismatch_detected"]:
            explanation_bullets.append(f"Headline-Body semantic mismatch: Headline keywords are weakly reflected in the body content.")

        if active_pred["prediction_class"] == 1:
            explanation_bullets.append(f"Model ({chosen_model_key}) identified high TF-IDF feature correlation with known misinformation patterns.")
        else:
            explanation_bullets.append(f"Model ({chosen_model_key}) identified linguistic markers and attribution typical of verified reporting.")

        # Boolean Fake News Decision
        is_fake_decision = bool(active_pred["prob_fake"] >= 0.50 or risk_profile["composite_risk_score"] >= 50.0)
        fake_pct = round(active_pred["prob_fake"] * 100, 1)
        real_pct = round(active_pred["prob_real"] * 100, 1)

        return {
            "verdict": verdict_data["verdict"],
            "verdict_badge_color": verdict_data["badge_color"],
            "verdict_summary": verdict_data["summary"],
            "is_fake": is_fake_decision,
            "fake_percentage": fake_pct,
            "real_percentage": real_pct,
            "model_confidence": active_pred["confidence"],
            "misinformation_risk_score": risk_profile["composite_risk_score"],
            "prob_fake": active_pred["prob_fake"],
            "prob_real": active_pred["prob_real"],
            "active_model": {
                "key": chosen_model_key,
                "name": self.metrics.get("models", {}).get(chosen_model_key, {}).get("name", chosen_model_key),
                "type": self.metrics.get("models", {}).get(chosen_model_key, {}).get("type", "Classifier"),
                "accuracy": self.metrics.get("models", {}).get(chosen_model_key, {}).get("accuracy", 0.99),
                "f1_score": self.metrics.get("models", {}).get(chosen_model_key, {}).get("f1_score", 0.0)
            },
            "linguistic_risk": risk_profile,
            "xai_explanation": xai_explanation,
            "highlighted_analysis": highlight_data,
            "text_statistics": stats,
            "multi_model_comparison": comparison_results,
            "explanation_bullets": explanation_bullets,
            "disclaimer": "Notice: Model confidence represents learned statistical classification probability based on training patterns, not philosophical or factual certainty."
        }

model_service = ModelService()
