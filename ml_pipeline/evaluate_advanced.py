"""
Sprint 2 Evaluation: Evaluate Advanced Model on Held-Out Test Split.
"""
from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))
_ML_DIR = _PROJECT_ROOT / "ml_pipeline"
if str(_ML_DIR) not in sys.path:
    sys.path.insert(0, str(_ML_DIR))

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score, precision_score, recall_score

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

PROCESSED_DIR = _PROJECT_ROOT / "data" / "processed"
MODELS_DIR = _PROJECT_ROOT / "models"
CLASS_NAMES = ["No Fit", "Potential Fit", "Good Fit"]


def main():
    test_path = PROCESSED_DIR / "test.csv"
    model_path = MODELS_DIR / "advanced_pipeline_v2.joblib"
    if not model_path.exists():
        logger.error("Advanced model artifact not found at %s", model_path)
        return

    logger.info("Loading test data from %s...", test_path.name)
    test_df = pd.read_csv(test_path)
    logger.info("Loaded %d test samples.", len(test_df))

    logger.info("Loading advanced model from %s...", model_path.name)
    artifact = joblib.load(model_path)
    clf = artifact["classifier"]
    extractor = artifact["feature_extractor"]

    logger.info("Transforming test features...")
    X_test = extractor.transform(test_df["resume"].tolist(), test_df["jd"].tolist())
    y_test = test_df["label_encoded"].values

    logger.info("Predicting...")
    preds = clf.predict(X_test)

    acc = accuracy_score(y_test, preds)
    macro_f1 = f1_score(y_test, preds, average="macro", zero_division=0)
    weighted_f1 = f1_score(y_test, preds, average="weighted", zero_division=0)
    macro_p = precision_score(y_test, preds, average="macro", zero_division=0)
    macro_r = recall_score(y_test, preds, average="macro", zero_division=0)

    print("=" * 60)
    print("SPRINT 2 ADVANCED MODEL EVALUATION ON HELD-OUT TEST SPLIT")
    print("=" * 60)
    print(f"Overall Accuracy:  {acc * 100:.2f}%")
    print(f"Macro Precision:   {macro_p * 100:.2f}%")
    print(f"Macro Recall:      {macro_r * 100:.2f}%")
    print(f"Macro F1-Score:    {macro_f1 * 100:.2f}%")
    print(f"Weighted F1-Score: {weighted_f1 * 100:.2f}%")
    print("\nClassification Report:\n", classification_report(y_test, preds, target_names=CLASS_NAMES, zero_division=0))
    print("Confusion Matrix:\n", confusion_matrix(y_test, preds))
    print("=" * 60)
    print("[OK] Evaluation completed successfully.")


if __name__ == "__main__":
    main()

