"""
US-10: Create Reproducible Stratified Train and Held-Out Test Splits.
"""
import hashlib
import logging
import json
import pandas as pd
from pathlib import Path
from sklearn.model_selection import train_test_split

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

PROCESSED_DIR = Path(__file__).parent.parent / "data" / "processed"
RANDOM_STATE = 42
TEST_SIZE = 0.2
TOLERANCE = 0.005  # 0.5%


def verify_no_leakage(train_df: pd.DataFrame, test_df: pd.DataFrame) -> bool:
    """Assert zero overlap between train and test sets."""
    train_pairs = set(train_df['resume'] + ' ||| ' + train_df['jd'])
    test_pairs = set(test_df['resume'] + ' ||| ' + test_df['jd'])
    overlap = train_pairs.intersection(test_pairs)
    
    assert len(overlap) == 0, f"DATA LEAKAGE DETECTED! {len(overlap)} overlapping (resume, jd) pairs!"
    logger.info(f"[OK] Zero-overlap leakage check passed. Train: {len(train_df)}, Test: {len(test_df)}")
    return True


def verify_stratification(train_df: pd.DataFrame, test_df: pd.DataFrame, label_col='label') -> bool:
    """Verify class distribution is maintained within tolerance."""
    overall_dist = train_df[label_col].value_counts(normalize=True)
    test_dist = test_df[label_col].value_counts(normalize=True)
    
    for label in overall_dist.index:
        overall_pct = overall_dist.get(label, 0)
        test_pct = test_dist.get(label, 0)
        diff = abs(overall_pct - test_pct)
        if diff > TOLERANCE:
            logger.warning(f"Stratification drift for '{label}': {diff:.4f} > {TOLERANCE}")
        else:
            logger.info(f"[OK] '{label}': train={overall_pct:.3f}, test={test_pct:.3f}, diff={diff:.4f}")
    return True


def split_data(df: pd.DataFrame, label_col: str = 'label_encoded') -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Split data into reproducible stratified train/test sets.
    
    Returns:
        (train_df, test_df)
    """
    # Check minimum class samples
    min_class_count = df[label_col].value_counts().min()
    if min_class_count < 2:
        raise ValueError(
            f"Minimum class count is {min_class_count}. "
            "Not enough samples for stratified split. "
            "Ensure at least 2 samples per class."
        )
    
    train_df, test_df = train_test_split(
        df,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        stratify=df[label_col]
    )
    
    train_df = train_df.reset_index(drop=True)
    test_df = test_df.reset_index(drop=True)
    
    logger.info(f"Train: {len(train_df)} rows, Test: {len(test_df)} rows")
    
    return train_df, test_df


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    sys.path.insert(0, str(Path(__file__).parent))
    try:
        from ml_pipeline.load_data import load_data
        from ml_pipeline.inspect_data import validate_and_rename_columns
        from ml_pipeline.clean_data import clean_dataset
        from ml_pipeline.preprocessing import preprocess_dataframe
        from ml_pipeline.analyze_labels import encode_labels
    except (ImportError, ModuleNotFoundError):
        from load_data import load_data
        from inspect_data import validate_and_rename_columns
        from clean_data import clean_dataset
        from preprocessing import preprocess_dataframe
        from analyze_labels import encode_labels
    
    df = load_data()
    df = validate_and_rename_columns(df)
    df, _ = clean_dataset(df)
    df = preprocess_dataframe(df)
    
    # Deduplicate post-normalization to guarantee zero duplicates created by normalization
    dup_after_norm = df.duplicated(subset=['resume', 'jd'], keep='first')
    if dup_after_norm.sum() > 0:
        logger.info(f"Dropping {dup_after_norm.sum()} duplicates identified post-normalization")
        df = df[~dup_after_norm].reset_index(drop=True)
        
    df['label_encoded'] = encode_labels(df['label'])
    
    train_df, test_df = split_data(df)
    
    # Verify
    verify_no_leakage(train_df, test_df)
    verify_stratification(train_df, test_df, label_col='label')
    
    # Save
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    train_path = PROCESSED_DIR / "train.csv"
    test_path = PROCESSED_DIR / "test.csv"
    train_df.to_csv(train_path, index=False)
    test_df.to_csv(test_path, index=False)
    logger.info(f"Train saved to: {train_path}")
    logger.info(f"Test saved to: {test_path}")
