"""Model Registry for loading and caching the ML artifact."""

import json
import os
from typing import Any, Dict, Optional

import joblib

from app.core.config import settings
from app.core.logging import logger


class ModelRegistry:
    """Singleton registry for managing the active ML model artifact."""

    _instance: Optional["ModelRegistry"] = None

    def __new__(cls) -> "ModelRegistry":
        if cls._instance is None:
            cls._instance = super(ModelRegistry, cls).__new__(cls)
            cls._instance._model_artifact = None
            cls._instance._metadata = None
            cls._instance._load_model()
        return cls._instance

    def _load_model(self) -> None:
        """Load model artifact from configured path if it exists."""
        model_path = settings.ML_MODEL_PATH
        meta_path = settings.ML_METADATA_PATH

        if os.path.exists(model_path):
            try:
                self._model_artifact = joblib.load(model_path)
                logger.info(
                    f"Loaded ML model version {self._model_artifact.get('model_version', 'unknown')} from {model_path}"
                )
            except Exception as e:
                logger.error(f"Failed to load ML model artifact from {model_path}: {e}")
                self._model_artifact = None
        else:
            logger.warning(
                f"ML model artifact not found at {model_path}. Fallback inference will be used until trained."
            )
            self._model_artifact = None

        if os.path.exists(meta_path):
            try:
                with open(meta_path, "r", encoding="utf-8") as f:
                    self._metadata = json.load(f)
            except Exception as e:
                logger.warning(f"Could not load metadata from {meta_path}: {e}")
                self._metadata = None

    def reload(self) -> bool:
        """Force reload of the model artifact from disk."""
        self._load_model()
        return self.is_loaded()

    def is_loaded(self) -> bool:
        """Check if model artifact is actively loaded."""
        return self._model_artifact is not None

    def get_artifact(self) -> Optional[Dict[str, Any]]:
        """Get the loaded artifact dictionary."""
        return self._model_artifact

    def get_metadata(self) -> Optional[Dict[str, Any]]:
        """Get model metadata."""
        return self._metadata

    def get_model_version(self) -> str:
        """Return model version or fallback."""
        if self._model_artifact:
            return str(self._model_artifact.get("model_version", "v1.0.0"))
        return "v0.0.0-heuristic"


def get_model_registry() -> ModelRegistry:
    """Get the singleton ModelRegistry instance."""
    return ModelRegistry()
