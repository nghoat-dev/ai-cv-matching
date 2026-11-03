"""
US-12: Train, Validate, and Serialize a Reproducible Baseline ML Model.
"""
import json
import logging
import datetime
import numpy as np
import pandas as pd
import joblib
import sklearn
from pathlib import Path
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

MODELS_DIR = Path(__file__).parent.parent / "models"
PROCESSED_DIR = Path(__file__).parent.parent / "data" / "processed"
RANDOM_STATE = 42


class ModelLoadError(Exception):
    pass


def compute_matching_score(probabilities: np.ndarray, cosine_similarities: np.ndarray = None) -> np.ndarray:
    """
    Deterministic formula mapping class probabilities to 0-100 score.
    
    Formula: score = P(Good Fit) * 100 * 0.7 + P(Potential Fit) * 100 * 0.4 + cosine_sim * 30
    Falls back to probability-only if cosine_sim not provided.
    
    Returns values strictly within [0.0, 100.0].
    """
    p_no_fit = probabilities[:, 0]
    p_potential = probabilities[:, 1]
    p_good_fit = probabilities[:, 2]
    
    if cosine_similarities is not None:
        score = p_good_fit * 70 + p_potential * 40 + cosine_similarities * 30
    else:
        score = p_good_fit * 80 + p_potential * 30 + (1 - p_no_fit) * 20 * 0.5
    
    # Clip to [0, 100]
    score = np.clip(score, 0.0, 100.0)
    return score


def train_baseline(X_train, y_train) -> LogisticRegression:
    """Train reproducible baseline Logistic Regression classifier."""
    logger.info("Training baseline Logistic Regression model...")
    clf = LogisticRegression(
        random_state=RANDOM_STATE,
        max_iter=1000,
        class_weight='balanced',
        solver='lbfgs',
        C=1.0,
    )
    clf.fit(X_train, y_train)
    logger.info("[OK] Model training complete")
    return clf


def save_model_artifact(clf, extractor, metadata: dict, path: Path):
    """Serialize model + feature extractor bundle with metadata."""
    artifact = {
        'classifier': clf,
        'feature_extractor': extractor,
        'metadata': metadata,
    }
    joblib.dump(artifact, path)
    logger.info(f"Model artifact saved to: {path}")


def load_model_artifact(path: Path) -> dict:
    """Load model artifact with proper error handling."""
    try:
        artifact = joblib.load(path)
        logger.info(f"Model artifact loaded from: {path}")
        return artifact
    except FileNotFoundError:
        raise ModelLoadError(f"Model artifact not found at: {path}")
    except EOFError:
        raise ModelLoadError(f"Model artifact corrupted/truncated at: {path}")
    except Exception as e:
        raise ModelLoadError(f"Failed to load model artifact: {e}")


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    sys.path.insert(0, str(Path(__file__).parent))
    try:
        from ml_pipeline.feature_extraction import FeatureExtractor
    except (ImportError, ModuleNotFoundError):
        from feature_extraction import FeatureExtractor
    
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Load splits
    train_df = pd.read_csv(PROCESSED_DIR / "train.csv")
    logger.info(f"Train set: {len(train_df)} rows")
    
    # Extract features
    extractor = FeatureExtractor()
    X_train = extractor.fit_transform(train_df['resume'].tolist(), train_df['jd'].tolist())
    y_train = train_df['label_encoded'].values
    
    # Train
    clf = train_baseline(X_train, y_train)
    
    # Validate predict / predict_proba
    sample_preds = clf.predict(X_train[:10])
    sample_probas = clf.predict_proba(X_train[:10])
    assert set(sample_preds).issubset({0, 1, 2}), "Predictions contain invalid class IDs!"
    assert sample_probas.shape == (10, 3), "predict_proba shape mismatch!"
    assert np.allclose(sample_probas.sum(axis=1), 1.0), "Probabilities don't sum to 1!"
    logger.info("[OK] predict and predict_proba validated")
    
    # Test scoring formula monotonicity
    high_score = compute_matching_score(np.array([[0.05, 0.10, 0.85]]))[0]
    low_score = compute_matching_score(np.array([[0.75, 0.10, 0.15]]))[0]
    assert high_score > low_score, f"Scoring not monotonic! {high_score} <= {low_score}"
    assert 0.0 <= high_score <= 100.0
    assert 0.0 <= low_score <= 100.0
    logger.info(f"[OK] Scoring formula validated. High={high_score:.1f}, Low={low_score:.1f}")
    
    # Metadata
    metadata = {
        'training_timestamp': datetime.datetime.now().isoformat(),
        'sklearn_version': sklearn.__version__,
        'feature_count': X_train.shape[1],
        'training_samples': len(train_df),
        'random_state': RANDOM_STATE,
        'model_type': 'LogisticRegression',
        'version': 'v1',
    }
    
    # Save artifact
    artifact_path = MODELS_DIR / "baseline_pipeline_v1.joblib"
    save_model_artifact(clf, extractor, metadata, artifact_path)
    
    # Verify reload
    loaded = load_model_artifact(artifact_path)
    loaded_clf = loaded['classifier']
    loaded_preds = loaded_clf.predict(X_train[:50])
    original_preds = clf.predict(X_train[:50])
    assert np.array_equal(loaded_preds, original_preds), "Loaded model predictions differ!"
    logger.info("[OK] Model reload and prediction consistency verified")
    logger.info(f"Metadata: {metadata}")
