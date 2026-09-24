import os
import sys
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))


def evaluate_disease_model():
    meta_path = BASE_DIR / "models" / "disease_metadata.json"
    if not meta_path.exists():
        from ml.disease.train import train_disease_random_forest
        metadata = train_disease_random_forest()
    else:
        with open(meta_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)

    print("=" * 70)
    print("  DNAura — Disease Prediction Random Forest Evaluation Summary")
    print("=" * 70)
    print(f"Algorithm:       {metadata.get('algorithm')}")
    print(f"Number of Classes: {len(metadata.get('classes', []))}")
    print(f"Classes:         {', '.join(metadata.get('classes', []))}")
    print(f"Test Samples:    {metadata.get('test_samples')}")
    print(f"Test Accuracy:   {metadata['metrics']['accuracy']}%")
    print(f"Weighted F1:     {metadata['metrics']['f1_score']}%")
    print(f"Weighted Precision: {metadata['metrics']['precision']}%")
    print(f"Weighted Recall: {metadata['metrics']['recall']}%")

    print("\nConfusion Matrix (5x5):")
    labels = metadata["confusion_matrix"]["labels"]
    matrix = metadata["confusion_matrix"]["matrix"]
    print(" " * 22 + " ".join(f"[{lbl[:5]:5s}]" for lbl in labels))
    for i, row in enumerate(matrix):
        print(f"[{labels[i]:20s}] " + " ".join(f"{val:7d}" for val in row))

    print("\nClassification Report:")
    report = metadata["classification_report"]
    for cls in labels:
        if cls in report:
            c_data = report[cls]
            print(f"  - {cls:22s}: Precision={c_data['precision']*100:.1f}%, Recall={c_data['recall']*100:.1f}%, F1={c_data['f1-score']*100:.1f}%, Support={c_data['support']}")

    return metadata


if __name__ == "__main__":
    evaluate_disease_model()
