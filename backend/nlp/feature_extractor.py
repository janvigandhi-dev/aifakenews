import joblib
from pathlib import Path
from typing import List, Dict, Any, Union
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

class FeatureExtractor:
    def __init__(self, max_features: int = 15000, ngram_range: tuple = (1, 2)):
        self.vectorizer = TfidfVectorizer(
            ngram_range=ngram_range,
            max_features=max_features,
            sublinear_tf=True,
            min_df=2,
            max_df=0.95,
            norm='l2'
        )
        self.is_fitted = False

    def fit(self, texts: List[str]):
        """Fits TF-IDF vectorizer on preprocessed text documents."""
        self.vectorizer.fit(texts)
        self.is_fitted = True
        return self

    def transform(self, texts: List[str]):
        """Transforms preprocessed texts into sparse TF-IDF feature matrix."""
        if not self.is_fitted:
            raise ValueError("Vectorizer must be fitted before transforming texts.")
        return self.vectorizer.transform(texts)

    def fit_transform(self, texts: List[str]):
        """Fits vectorizer and transforms documents in one step."""
        X = self.vectorizer.fit_transform(texts)
        self.is_fitted = True
        return X

    def get_feature_names(self) -> List[str]:
        """Returns vocabulary feature names."""
        if not self.is_fitted:
            return []
        return self.vectorizer.get_feature_names_out().tolist()

    def save(self, filepath: Union[str, Path]):
        """Serializes vectorizer to disk."""
        joblib.dump(self.vectorizer, filepath)

    def load(self, filepath: Union[str, Path]):
        """Loads fitted vectorizer from disk."""
        self.vectorizer = joblib.load(filepath)
        self.is_fitted = True
        return self
