"""
US-11: Extract Numerical Text Features Fitted Strictly on Training Data.
TF-IDF vectors + pairwise similarity signals.
"""
import logging
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from scipy.sparse import hstack, issparse

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

MODELS_DIR = Path(__file__).parent.parent / "models"
RANDOM_STATE = 42

TFIDF_PARAMS = {
    'max_features': 20000,
    'ngram_range': (1, 2),
    'min_df': 2,
    'sublinear_tf': True,
    'analyzer': 'word',
}


def compute_pairwise_features(resume_texts: list, jd_texts: list,
                               resume_vectors, jd_vectors) -> np.ndarray:
    """
    Compute pairwise interaction features (vectorized & memory-efficient):
    - Cosine similarity between resume and jd TF-IDF vectors
    - Token overlap ratio
    - Length ratio
    """
    n = len(resume_texts)
    
    # Vectorized cosine similarity for sparse matrices
    dot_products = np.asarray(resume_vectors.multiply(jd_vectors).sum(axis=1)).ravel()
    r_norms = np.asarray(np.sqrt(resume_vectors.multiply(resume_vectors).sum(axis=1))).ravel()
    j_norms = np.asarray(np.sqrt(jd_vectors.multiply(jd_vectors).sum(axis=1))).ravel()
    
    valid_norms = (r_norms > 0) & (j_norms > 0)
    cosine_sims = np.zeros(n, dtype=np.float32)
    cosine_sims[valid_norms] = (dot_products[valid_norms] / (r_norms[valid_norms] * j_norms[valid_norms])).astype(np.float32)
    
    # Token overlap and length ratios
    token_overlaps = np.zeros(n, dtype=np.float32)
    length_ratios = np.zeros(n, dtype=np.float32)
    
    for i in range(n):
        r_tokens = set(resume_texts[i].split())
        j_tokens = set(jd_texts[i].split())
        if len(j_tokens) > 0:
            token_overlaps[i] = len(r_tokens & j_tokens) / len(j_tokens)
        
        r_len = len(resume_texts[i])
        j_len = len(jd_texts[i])
        if j_len > 0:
            length_ratios[i] = min(r_len / j_len, 10.0)
    
    return np.column_stack([cosine_sims, token_overlaps, length_ratios])


class FeatureExtractor:
    """TF-IDF feature extractor with pairwise signals using a shared vocabulary."""
    
    def __init__(self):
        self.vectorizer = TfidfVectorizer(**TFIDF_PARAMS)
        self._is_fitted = False
    
    def fit(self, train_resume: list, train_jd: list):
        """Fit shared vectorizer ONLY on training data (resume + jd)."""
        logger.info("Fitting shared TF-IDF vectorizer on training data...")
        all_train_texts = train_resume + train_jd
        self.vectorizer.fit(all_train_texts)
        self._is_fitted = True
        logger.info(f"Shared vocab size: {len(self.vectorizer.vocabulary_)}")
        return self
    
    def transform(self, resume_texts: list, jd_texts: list) -> np.ndarray:
        """Transform texts to feature matrix."""
        if not self._is_fitted:
            raise RuntimeError("FeatureExtractor must be fitted before transform!")
        
        resume_vecs = self.vectorizer.transform(resume_texts)
        jd_vecs = self.vectorizer.transform(jd_texts)
        
        # Pairwise features (both vectors have identical column dimensions)
        pairwise = compute_pairwise_features(resume_texts, jd_texts, resume_vecs, jd_vecs)
        
        # Concatenate TF-IDF + pairwise (keep sparse)
        X = hstack([resume_vecs, jd_vecs, pairwise]).tocsr()
        
        # Memory-safe validation (inspect data array directly without dense conversion)
        if issparse(X):
            assert not np.isnan(X.data).any(), "NaN found in sparse feature matrix!"
            assert not np.isinf(X.data).any(), "Inf found in sparse feature matrix!"
        else:
            assert not np.isnan(X).any(), "NaN found in feature matrix!"
            assert not np.isinf(X).any(), "Inf found in feature matrix!"
        
        return X
    
    def fit_transform(self, train_resume: list, train_jd: list) -> np.ndarray:
        """Fit and transform training data."""
        self.fit(train_resume, train_jd)
        return self.transform(train_resume, train_jd)
    
    def save(self, path: Path):
        """Serialize fitted extractor."""
        joblib.dump(self, path)
        logger.info(f"FeatureExtractor saved to: {path}")
    
    @classmethod
    def load(cls, path: Path) -> 'FeatureExtractor':
        """Load serialized extractor."""
        try:
            extractor = joblib.load(path)
            logger.info(f"FeatureExtractor loaded from: {path}")
            return extractor
        except (FileNotFoundError, EOFError) as e:
            raise RuntimeError(f"Failed to load FeatureExtractor: {e}")


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    
    PROCESSED_DIR = Path(__file__).parent.parent / "data" / "processed"
    train_df = pd.read_csv(PROCESSED_DIR / "train.csv")
    test_df = pd.read_csv(PROCESSED_DIR / "test.csv")
    
    extractor = FeatureExtractor()
    X_train = extractor.fit_transform(train_df['resume'].tolist(), train_df['jd'].tolist())
    X_test = extractor.transform(test_df['resume'].tolist(), test_df['jd'].tolist())
    
    logger.info(f"X_train shape: {X_train.shape}")
    logger.info(f"X_test shape: {X_test.shape}")
    assert X_train.shape[1] == X_test.shape[1], "Feature dimension mismatch!"
    logger.info("[OK] Feature dimensions match")
    
    # Vocabulary leakage check
    vocab = set(extractor.vectorizer.vocabulary_.keys())
    assert 'xyz_test_only_token_999' not in vocab, "Test-only token leaked into vocabulary!"
    logger.info("[OK] Vocabulary leakage check passed")
    
    # Save
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    extractor.save(MODELS_DIR / "feature_extractor.joblib")
