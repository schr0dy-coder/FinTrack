"""Data Preprocessing Pipeline for Anomaly Detection."""

import numpy as np
from sklearn.preprocessing import RobustScaler


class MLPreprocessor:
    """Preprocesses features using RobustScaler (resilient to heavy outliers)."""

    def __init__(self):
        self.scaler = RobustScaler()
        self.is_fitted = False

    def fit(self, X: np.ndarray) -> "MLPreprocessor":
        self.scaler.fit(X)
        self.is_fitted = True
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        if not self.is_fitted:
            return X
        return self.scaler.transform(X)

    def fit_transform(self, X: np.ndarray) -> np.ndarray:
        self.is_fitted = True
        return self.scaler.fit_transform(X)
