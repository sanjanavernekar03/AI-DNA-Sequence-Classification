import json
import joblib
import numpy as np
from pathlib import Path
from typing import Dict, Any

from app.config import Config
from app.services.dna_service import sanitize_dna
from app.ml.feature_extraction import extract_dna_feature_vector, get_feature_names

_clf_model = None
_clf_metadata = None


def get_classification_model():
    """Lazy load or train the classification model."""
    global _clf_model, _clf_metadata
    model_path = Config.MODELS_DIR / "dna_classifier.joblib"
    meta_path = Config.MODELS_DIR / "classification_metadata.json"

    if _clf_model is None or _clf_metadata is None:
        if not model_path.exists() or not meta_path.exists():
            from app.ml.train_classification import train_dna_classifier
            train_dna_classifier()

        _clf_model = joblib.load(model_path)
        with open(meta_path, "r", encoding="utf-8") as f:
            _clf_metadata = json.load(f)

    return _clf_model, _clf_metadata


def predict_dna_class(sequence: str) -> Dict[str, Any]:
    """
    Run machine learning classification on a DNA sequence.
    Returns: predicted class, confidence %, class probabilities, top extracted features, model metrics.
    """
    cleaned = sanitize_dna(sequence)
    model, metadata = get_classification_model()

    features_vec = extract_dna_feature_vector(cleaned).reshape(1, -1)
    predicted_class = model.predict(features_vec)[0]

    # Predict probabilities
    probabilities = {}
    confidence = 0.0
    if hasattr(model, "predict_proba"):
        probs = model.predict_proba(features_vec)[0]
        for cls_name, prob in zip(model.classes_, probs):
            probabilities[cls_name] = round(float(prob) * 100.0, 2)
        confidence = probabilities.get(predicted_class, round(float(np.max(probs)) * 100.0, 2))
    else:
        confidence = 90.0

    # Extract notable feature statistics for display
    feature_names = get_feature_names()
    feat_dict = {}
    for i, name in enumerate(feature_names[:15]):  # First 15 key features
        feat_dict[name] = round(float(features_vec[0][i]), 4)

    return {
        "predicted_class": predicted_class,
        "confidence": confidence,
        "probabilities": probabilities,
        "model_name": metadata.get("model_name", "RandomForestClassifier"),
        "metrics": metadata.get("metrics", {}),
        "confusion_matrix": metadata.get("confusion_matrix", {}),
        "top_features": metadata.get("top_features", []),
        "extracted_features_sample": feat_dict
    }
