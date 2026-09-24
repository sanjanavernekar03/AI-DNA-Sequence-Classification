import os
import sys
import json
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score, RandomizedSearchCV
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, precision_recall_fscore_support
import joblib

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

from ml.disease.preprocess import create_and_preprocess_dataset
from ml.disease.feature_extraction import extract_disease_feature_vector, get_disease_feature_names


def train_disease_random_forest():
    """
    Train, evaluate, tune, and save the primary Random Forest Disease Prediction model.
    """
    print("=" * 70)
    print("  DNAura — 5-Class Disease Random Forest Classifier Training Pipeline")
    print("=" * 70)

    # 1. Load / Prepare Processed Dataset
    proc_path = BASE_DIR / "dataset" / "disease_prediction" / "processed" / "processed_dataset.csv"
    if not proc_path.exists():
        print("Processed dataset not found. Running preprocessing pipeline...")
        df = create_and_preprocess_dataset(samples_per_class=300)
    else:
        df = pd.read_csv(proc_path)
        print(f"Loaded existing processed dataset from {proc_path} ({len(df)} samples)")

    # 2. Extract Feature Space
    print("\nExtracting 89-dimensional biological and k-mer feature vectors...")
    feature_matrix = []
    for seq in df["sequence"].tolist():
        vec = extract_disease_feature_vector(seq)
        feature_matrix.append(vec)

    X = np.array(feature_matrix, dtype=np.float64)
    y = np.array([str(item) for item in df["disease_category"].tolist()], dtype=str)

    print(f"Feature matrix shape: {X.shape}, Target labels shape: {y.shape}")

    # 3. Stratified Train / Test Split (75% Train, 25% Held-out Test)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y
    )
    print(f"Training set: {X_train.shape[0]} samples | Held-out test set: {X_test.shape[0]} samples")

    # 4. Tune Random Forest Classifier via RandomizedSearchCV
    print("\nTuning Random Forest Classifier via RandomizedSearchCV...")
    base_rf = RandomForestClassifier(class_weight="balanced", random_state=42, n_jobs=-1)
    
    param_dist = {
        'n_estimators': [100, 200, 300],
        'max_depth': [10, 18, 25, None],
        'min_samples_split': [2, 3, 5],
        'min_samples_leaf': [1, 2, 4],
        'max_features': ['sqrt', 'log2']
    }
    
    random_search = RandomizedSearchCV(
        estimator=base_rf,
        param_distributions=param_dist,
        n_iter=10,
        cv=3,
        scoring='accuracy',
        random_state=42,
        n_jobs=-1
    )
    
    print("Fitting RandomizedSearchCV (this may take a moment)...")
    random_search.fit(X_train, y_train)
    
    rf_model = random_search.best_estimator_
    print(f"Best Hyperparameters: {random_search.best_params_}")

    # 5-fold cross-validation on training split
    cv_scores = cross_val_score(rf_model, X_train, y_train, cv=5, scoring="accuracy")
    print(f"5-Fold Cross-Validation Accuracy: {cv_scores.mean()*100:.2f}% (+/- {cv_scores.std()*100:.2f}%)")

    # 5. Held-out Evaluation
    y_pred = rf_model.predict(X_test)
    y_proba = rf_model.predict_proba(X_test)

    acc = float(accuracy_score(y_test, y_pred))
    p_weighted, r_weighted, f1_weighted, _ = precision_recall_fscore_support(y_test, y_pred, average="weighted")
    p_macro, r_macro, f1_macro, _ = precision_recall_fscore_support(y_test, y_pred, average="macro")

    classes = [str(c) for c in rf_model.classes_]
    cm = confusion_matrix(y_test, y_pred, labels=rf_model.classes_).tolist()
    report_dict = classification_report(y_test, y_pred, target_names=classes, output_dict=True)

    print("\n" + "-" * 70)
    print(f"  HELD-OUT TEST SET EVALUATION METRICS:")
    print(f"  - Accuracy:         {acc * 100:.2f}%")
    print(f"  - Weighted F1:      {f1_weighted * 100:.2f}%")
    print(f"  - Macro F1:         {f1_macro * 100:.2f}%")
    print(f"  - Weighted Precision:{p_weighted * 100:.2f}%")
    print(f"  - Weighted Recall:   {r_weighted * 100:.2f}%")
    print("-" * 70)

    # Print Per-Class Metrics
    print("\nPer-Class Breakdown:")
    for cls in classes:
        cls_metrics = report_dict.get(cls, {})
        print(f"  [{cls:22s}] Precision: {cls_metrics.get('precision', 0)*100:.1f}% | Recall: {cls_metrics.get('recall', 0)*100:.1f}% | F1: {cls_metrics.get('f1-score', 0)*100:.1f}% | Support: {cls_metrics.get('support', 0)}")

    # 6. Feature Importances
    feature_names = get_disease_feature_names()
    importances = rf_model.feature_importances_
    top_indices = np.argsort(importances)[::-1][:12]
    top_features = [{"feature": feature_names[i], "importance": round(float(importances[i]), 4)} for i in top_indices]

    # 7. Metadata Object
    metadata = {
        "model_name": "Disease Random Forest Classifier",
        "algorithm": "RandomForestClassifier (Ensemble Decision Trees)",
        "version": "1.0",
        "dataset_name": "NCBI Curated Multi-Class Genomic Disease & Variant Sequence Dataset",
        "classes": classes,
        "metrics": {
            "accuracy": round(acc * 100.0, 2),
            "precision": round(float(p_weighted) * 100.0, 2),
            "recall": round(float(r_weighted) * 100.0, 2),
            "f1_score": round(float(f1_weighted) * 100.0, 2),
            "macro_f1": round(float(f1_macro) * 100.0, 2),
            "macro_precision": round(float(p_macro) * 100.0, 2),
            "macro_recall": round(float(r_macro) * 100.0, 2),
            "cv_accuracy_mean": round(float(cv_scores.mean()) * 100.0, 2),
            "cv_accuracy_std": round(float(cv_scores.std()) * 100.0, 2)
        },
        "confusion_matrix": {
            "labels": classes,
            "matrix": cm
        },
        "classification_report": report_dict,
        "top_features": top_features,
        "total_samples": len(df),
        "train_samples": len(X_train),
        "test_samples": len(X_test),
        "feature_count": X.shape[1],
        "disclaimer_notice": "This system provides AI-based predictions for academic and research purposes only. It is not a medical diagnostic system and should not be used to make medical decisions."
    }

    # 8. Save Models and Metadata to both `models/` and `app/ml/models/`
    dest_dirs = [
        BASE_DIR / "models",
        BASE_DIR / "app" / "ml" / "models"
    ]
    for d in dest_dirs:
        os.makedirs(d, exist_ok=True)
        joblib.dump(rf_model, d / "disease_random_forest.joblib")
        joblib.dump(rf_model, d / "disease_predictor.joblib")
        with open(d / "disease_metadata.json", "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

    print(f"\nModel artifacts successfully written to: {dest_dirs[0]} and {dest_dirs[1]}")
    return metadata


if __name__ == "__main__":
    train_disease_random_forest()
