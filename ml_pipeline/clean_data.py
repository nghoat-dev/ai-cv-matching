"""
US-07: Filter Out Missing, Empty, Corrupted-Label, or Duplicate Records.
"""
import logging
import json
import pandas as pd
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

VALID_LABELS = {'Good Fit', 'Potential Fit', 'No Fit'}
LABEL_ALIASES = {
    'good fit': 'Good Fit',
    'good_fit': 'Good Fit',
    'potential fit': 'Potential Fit',
    'potential_fit': 'Potential Fit',
    'no fit': 'No Fit',
    'no_fit': 'No Fit',
}
MIN_TEXT_LENGTH = 15
REPORTS_DIR = Path(__file__).parent.parent / "reports"


def normalize_label(label) -> str | None:
    """Normalize label to canonical form."""
    if pd.isna(label):
        return None
    label_str = str(label).strip()
    if label_str in VALID_LABELS:
        return label_str
    normalized = LABEL_ALIASES.get(label_str.lower())
    return normalized  # None if not found


def clean_dataset(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """
    Clean dataset by removing invalid records.
    
    Returns:
        (cleaned_df, audit_log)
    """
    audit = {
        'initial_count': len(df),
        'dropped_null_resume': 0,
        'dropped_null_jd': 0,
        'dropped_null_label': 0,
        'dropped_empty_short_resume': 0,
        'dropped_empty_short_jd': 0,
        'dropped_invalid_label': 0,
        'dropped_exact_duplicates': 0,
        'dropped_conflicting_duplicates': 0,
        'final_count': 0,
    }
    
    df = df.copy()
    
    # 1. Drop null resume
    mask_null_resume = df['resume'].isna()
    audit['dropped_null_resume'] = int(mask_null_resume.sum())
    df = df[~mask_null_resume].reset_index(drop=True)
    
    # 2. Drop null jd
    mask_null_jd = df['jd'].isna()
    audit['dropped_null_jd'] = int(mask_null_jd.sum())
    df = df[~mask_null_jd].reset_index(drop=True)
    
    # 3. Drop null label
    mask_null_label = df['label'].isna()
    audit['dropped_null_label'] = int(mask_null_label.sum())
    df = df[~mask_null_label].reset_index(drop=True)
    
    # 4. Drop empty/short resume
    mask_short_resume = df['resume'].astype(str).str.strip().str.len() < MIN_TEXT_LENGTH
    audit['dropped_empty_short_resume'] = int(mask_short_resume.sum())
    df = df[~mask_short_resume].reset_index(drop=True)
    
    # 5. Drop empty/short jd
    mask_short_jd = df['jd'].astype(str).str.strip().str.len() < MIN_TEXT_LENGTH
    audit['dropped_empty_short_jd'] = int(mask_short_jd.sum())
    df = df[~mask_short_jd].reset_index(drop=True)
    
    # 6. Normalize and validate labels
    df['label'] = df['label'].apply(normalize_label)
    mask_invalid_label = df['label'].isna()
    audit['dropped_invalid_label'] = int(mask_invalid_label.sum())
    df = df[~mask_invalid_label].reset_index(drop=True)
    
    # 7. Drop conflicting duplicates (same resume+jd, different labels)
    label_counts = df.groupby(['resume', 'jd'])['label'].transform('nunique')
    conflict_mask = label_counts > 1
    audit['dropped_conflicting_duplicates'] = int(conflict_mask.sum())
    df = df[~conflict_mask].reset_index(drop=True)
    
    # 8. Drop exact duplicates (keeping first)
    dup_mask = df.duplicated(subset=['resume', 'jd'], keep='first')
    audit['dropped_exact_duplicates'] = int(dup_mask.sum())
    df = df[~dup_mask].reset_index(drop=True)
    
    audit['final_count'] = len(df)
    
    # Log audit
    logger.info("=== Data Cleaning Audit ===")
    for k, v in audit.items():
        logger.info(f"  {k}: {v}")
    
    return df, audit


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    sys.path.insert(0, str(Path(__file__).parent))
    try:
        from ml_pipeline.load_data import load_data
        from ml_pipeline.inspect_data import validate_and_rename_columns
    except (ImportError, ModuleNotFoundError):
        from load_data import load_data
        from inspect_data import validate_and_rename_columns
    
    df = load_data()
    df = validate_and_rename_columns(df)
    
    cleaned_df, audit = clean_dataset(df)
    
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    audit_path = REPORTS_DIR / "cleaning_audit.json"
    with open(audit_path, 'w') as f:
        json.dump(audit, f, indent=2)
    
    logger.info(f"Audit log saved to: {audit_path}")
    logger.info(f"Clean dataset: {len(cleaned_df)} rows")
