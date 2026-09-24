import os
import sys
import json
import joblib
import numpy as np
from pathlib import Path
from typing import Dict, Any

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

from ml.disease.feature_extraction import extract_disease_feature_vector, get_disease_feature_names

_rf_disease_model = None
_rf_disease_meta = None


def load_disease_model():
    global _rf_disease_model, _rf_disease_meta
    model_path = BASE_DIR / "models" / "disease_random_forest.joblib"
    meta_path = BASE_DIR / "models" / "disease_metadata.json"

    # Fallback to app/ml/models if needed
    if not model_path.exists():
        model_path = BASE_DIR / "app" / "ml" / "models" / "disease_predictor.joblib"
        meta_path = BASE_DIR / "app" / "ml" / "models" / "disease_metadata.json"

    if not model_path.exists():
        from ml.disease.train import train_disease_random_forest
        _rf_disease_meta = train_disease_random_forest()
        _rf_disease_model = joblib.load(model_path)
    else:
        _rf_disease_model = joblib.load(model_path)
        with open(meta_path, "r", encoding="utf-8") as f:
            _rf_disease_meta = json.load(f)

    return _rf_disease_model, _rf_disease_meta


def predict_dna_disease(sequence: str) -> Dict[str, Any]:
    """
    Run 5-class Random Forest disease prediction on input DNA sequence.
    Returns: predicted_category, probability %, probabilities dict (5 classes),
    risk_category, sequence metrics summary, and academic disclaimer.
    """
    seq = sequence.strip().replace("\n", "").replace("\r", "").replace(" ", "").upper()
    model, metadata = load_disease_model()

    features_vec = extract_disease_feature_vector(seq).reshape(1, -1)
    predicted_class = str(model.predict(features_vec)[0])

    # Probability distribution across all 5 classes
    probabilities = {}
    probs = model.predict_proba(features_vec)[0]
    for cls_name, p in zip(model.classes_, probs):
        probabilities[str(cls_name)] = round(float(p) * 100.0, 2)

    top_prob = probabilities.get(predicted_class, round(float(np.max(probs)) * 100.0, 2))

    # Risk Category mapping
    if predicted_class == "Healthy":
        risk_category = "Low"
    elif top_prob >= 75.0:
        risk_category = "High"
    elif top_prob >= 50.0:
        risk_category = "Moderate"
    else:
        risk_category = "Low"

    # Summary metrics
    length = len(seq)
    gc_pct = round(((seq.count("G") + seq.count("C")) / length) * 100, 2) if length > 0 else 0.0
    at_pct = round(((seq.count("A") + seq.count("T")) / length) * 100, 2) if length > 0 else 0.0

    disclaimer = (
        "This system provides AI-based predictions for academic and research purposes only. "
        "It is not a medical diagnostic system and should not be used to make medical decisions."
    )

    feature_names = get_disease_feature_names()
    feat_sample = {}
    for i in range(min(12, len(feature_names))):
        feat_sample[feature_names[i]] = round(float(features_vec[0][i]), 4)

    return {
        "predicted_category": predicted_class,
        "probability": top_prob,
        "probabilities": probabilities,
        "risk_category": risk_category,
        "model_name": metadata.get("model_name", "Disease Random Forest Classifier"),
        "algorithm": metadata.get("algorithm", "RandomForestClassifier"),
        "version": metadata.get("version", "1.0"),
        "dataset_name": metadata.get("dataset_name", "NCBI Curated Multi-Class Genomic Disease Dataset"),
        "metrics": metadata.get("metrics", {}),
        "confusion_matrix": metadata.get("confusion_matrix", {}),
        "classification_report": metadata.get("classification_report", {}),
        "disclaimer_notice": disclaimer,
        "sequence_summary": {
            "length": length,
            "gc_content": gc_pct,
            "at_content": at_pct,
            "a_count": seq.count("A"),
            "t_count": seq.count("T"),
            "g_count": seq.count("G"),
            "c_count": seq.count("C")
        },
        "extracted_features_sample": feat_sample
    }


if __name__ == "__main__":
    test_seq = "ACTCCTGTGGAGAAGTCTGCCGTTACTGCCCTGTGGGGCAAGGTGAACGTGGATGAAGTTGGTGGTGAGGCCCTGGGCAGGCTGCTGGTGGTCTACCCTTGGACCCAGAGGTTCTTTGAGTCCTTTGGGGATCTGTCCACTCCTGATGCTGTTATGGGCAACCCTAAGGTGAAGGCTCATGGCAAGAAAGTGCTCGGTGCCTTTAGTGATGGCCTGGCT"
    res = predict_dna_disease(test_seq)
    print("Test Prediction Output:")
    print(f"Predicted:   {res['predicted_category']}")
    print(f"Probability: {res['probability']}%")
    print(f"Risk Tier:   {res['risk_category']}")
    print(f"All Scores:  {res['probabilities']}")
