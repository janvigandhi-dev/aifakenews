import json
import joblib
from pathlib import Path
from typing import Dict, Any, List
import pandas as pd
import numpy as np

from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import MultinomialNB
from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix, classification_report
)

from backend.config import DATA_DIR, SAVED_MODELS_DIR
from backend.nlp.preprocessor import preprocessor
from backend.nlp.feature_extractor import FeatureExtractor
from backend.models.dataset_builder import save_benchmark_dataset

class ModelTrainer:
    def __init__(self):
        self.feature_extractor = FeatureExtractor(max_features=12000, ngram_range=(1, 2))
        self.models: Dict[str, Any] = {}
        self.metrics: Dict[str, Any] = {}

    def load_or_generate_dataset(self) -> pd.DataFrame:
        """Loads existing CSV or generates a fresh balanced benchmark dataset."""
        dataset_path = DATA_DIR / "benchmark_dataset.csv"
        if not dataset_path.exists():
            save_benchmark_dataset()
        df = pd.read_csv(dataset_path)
        return df

    def preprocess_dataset(self, df: pd.DataFrame):
        """Combines headline and text and runs full NLP preprocessing."""
        combined_texts = []
        for _, row in df.iterrows():
            headline = str(row.get('headline', ''))
            body = str(row.get('text', ''))
            full_text = f"{headline}. {body}".strip()
            preprocessed = preprocessor.preprocess(full_text)
            combined_texts.append(preprocessed)
        return combined_texts, df['label'].values

    def train_all_models(self) -> Dict[str, Any]:
        """Trains and benchmarks 5 machine learning classifiers."""
        print("[Trainer] Starting dataset loading & preprocessing...")
        df = self.load_or_generate_dataset()
        texts, y = self.preprocess_dataset(df)

        # 70% Train, 15% Validation, 15% Test (Stratified)
        X_train_raw, X_temp_raw, y_train, y_temp = train_test_split(
            texts, y, test_size=0.30, random_state=42, stratify=y
        )
        X_val_raw, X_test_raw, y_val, y_test = train_test_split(
            X_temp_raw, y_temp, test_size=0.50, random_state=42, stratify=y_temp
        )

        print(f"[Trainer] Train: {len(X_train_raw)}, Val: {len(X_val_raw)}, Test: {len(X_test_raw)}")

        # Fit TF-IDF Feature Extractor on Training texts
        print("[Trainer] Fitting TF-IDF Vectorizer...")
        X_train = self.feature_extractor.fit_transform(X_train_raw)
        X_val = self.feature_extractor.transform(X_val_raw)
        X_test = self.feature_extractor.transform(X_test_raw)

        # Save fitted vectorizer
        self.feature_extractor.save(SAVED_MODELS_DIR / "tfidf_vectorizer.joblib")

        # Define 5 models
        classifiers = {
            "linear_svm": {
                "name": "Linear Support Vector Machine",
                "model": CalibratedClassifierCV(LinearSVC(C=1.0, random_state=42, max_iter=2000), cv=3),
                "type": "Support Vector Machine",
                "description": "High-dimensional maximum-margin hyperplane separator with Platt probability calibration."
            },
            "xgboost": {
                "name": "XGBoost Classifier",
                "model": XGBClassifier(n_estimators=120, max_depth=5, learning_rate=0.1, random_state=42, eval_metric="logloss"),
                "type": "Gradient Boosted Trees",
                "description": "State-of-the-art gradient boosted decision trees capturing non-linear term interactions."
            },
            "logistic_regression": {
                "name": "Logistic Regression",
                "model": LogisticRegression(C=1.5, max_iter=1000, random_state=42),
                "type": "Linear Generalized Model",
                "description": "Interpretable linear baseline providing log-odds feature coefficients and well-calibrated probabilities."
            },
            "naive_bayes": {
                "name": "Multinomial Naive Bayes",
                "model": MultinomialNB(alpha=0.1),
                "type": "Probabilistic Bayesian Model",
                "description": "Fast probabilistic generative classifier based on Bayes' theorem with term independence assumption."
            },
            "random_forest": {
                "name": "Random Forest",
                "model": RandomForestClassifier(n_estimators=100, max_depth=12, random_state=42),
                "type": "Ensemble Decision Forest",
                "description": "Bagging ensemble of randomized decision trees providing feature importance stability."
            }
        }

        all_results = {}
        best_model_key = None
        best_f1 = -1.0

        for key, conf in classifiers.items():
            print(f"[Trainer] Training {conf['name']} ({key})...")
            clf = conf["model"]
            clf.fit(X_train, y_train)

            # Evaluate on Test Set
            y_pred = clf.predict(X_test)
            if hasattr(clf, "predict_proba"):
                y_prob = clf.predict_proba(X_test)[:, 1]
            else:
                y_prob = y_pred

            acc = float(accuracy_score(y_test, y_pred))
            prec = float(precision_score(y_test, y_pred, average="weighted", zero_division=0))
            rec = float(recall_score(y_test, y_pred, average="weighted", zero_division=0))
            f1 = float(f1_score(y_test, y_pred, average="weighted", zero_division=0))
            try:
                roc_auc = float(roc_auc_score(y_test, y_prob))
            except Exception:
                roc_auc = 0.5

            cm = confusion_matrix(y_test, y_pred).tolist()
            # [[TN, FP], [FN, TP]]

            model_eval = {
                "key": key,
                "name": conf["name"],
                "type": conf["type"],
                "description": conf["description"],
                "accuracy": round(acc, 4),
                "precision": round(prec, 4),
                "recall": round(rec, 4),
                "f1_score": round(f1, 4),
                "roc_auc": round(roc_auc, 4),
                "confusion_matrix": {
                    "tn": cm[0][0] if len(cm) > 1 else cm[0][0],
                    "fp": cm[0][1] if len(cm) > 1 else 0,
                    "fn": cm[1][0] if len(cm) > 1 else 0,
                    "tp": cm[1][1] if len(cm) > 1 else 0,
                    "matrix": cm
                },
                "test_samples": len(y_test)
            }

            # Save model artifact
            model_path = SAVED_MODELS_DIR / f"{key}.joblib"
            joblib.dump(clf, model_path)
            all_results[key] = model_eval

            if f1 > best_f1:
                best_f1 = f1
                best_model_key = key

        # Benchmark summary
        benchmark_payload = {
            "version": "1.0.0",
            "dataset_name": "TruthLens Multi-Domain Benchmark Corpus",
            "total_samples": len(df),
            "train_samples": len(X_train_raw),
            "test_samples": len(X_test_raw),
            "best_model": best_model_key,
            "models": all_results
        }

        # Save metrics JSON
        with open(SAVED_MODELS_DIR / "metrics.json", "w") as f:
            json.dump(benchmark_payload, f, indent=2)

        print(f"[Trainer] Benchmark training complete! Best model: {best_model_key} (F1: {best_f1:.4f})")
        return benchmark_payload

trainer = ModelTrainer()

if __name__ == "__main__":
    trainer.train_all_models()
