"""
US-09: Analyze Label Distribution, Domain Frequencies, and Label Encoding.
"""
import json
import logging
import pandas as pd
import numpy as np
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

REPORTS_DIR = Path(__file__).parent.parent / "reports"
CONFIG_DIR = Path(__file__).parent / "config"

# Fixed, explicit label mapping (ordinal compatibility progression)
LABEL_MAPPING = {
    'No Fit': 0,
    'Potential Fit': 1,
    'Good Fit': 2,
}
INVERSE_LABEL_MAPPING = {v: k for k, v in LABEL_MAPPING.items()}

IMBALANCE_THRESHOLD_MIN_PCT = 20.0  # < 20% → flagged
IMBALANCE_RATIO_THRESHOLD = 1.5     # majority/minority > 1.5 → flagged


def encode_labels(label_series: pd.Series) -> pd.Series:
    """
    Encode labels to integers using fixed mapping.
    Raises ValueError for unmapped labels.
    """
    def _encode(label):
        if label not in LABEL_MAPPING:
            raise ValueError(f"Invalid label value: '{label}'. Expected one of {list(LABEL_MAPPING.keys())}")
        return LABEL_MAPPING[label]
    
    return label_series.apply(_encode)


def decode_labels(int_series: pd.Series) -> pd.Series:
    """Decode integer labels back to string labels."""
    return int_series.map(INVERSE_LABEL_MAPPING)


def analyze_label_distribution(df: pd.DataFrame) -> dict:
    """Analyze class distribution and detect imbalance."""
    counts = df['label'].value_counts()
    total = len(df)
    
    distribution = {}
    for label in ['Good Fit', 'Potential Fit', 'No Fit']:
        count = int(counts.get(label, 0))
        pct = round(count / total * 100, 2) if total > 0 else 0.0
        distribution[label] = {'count': count, 'percentage': pct}
    
    # Imbalance detection
    percentages = [v['percentage'] for v in distribution.values()]
    minority_pct = min(percentages)
    majority_pct = max(percentages)
    ratio = round(majority_pct / minority_pct, 2) if minority_pct > 0 else float('inf')
    
    is_imbalanced = minority_pct < IMBALANCE_THRESHOLD_MIN_PCT or ratio > IMBALANCE_RATIO_THRESHOLD
    
    if is_imbalanced:
        logger.warning(f"CLASS IMBALANCE DETECTED! Minority: {minority_pct:.1f}%, Ratio: {ratio:.2f}")
        logger.warning("→ Mandating stratified splits and class_weight='balanced' / Macro-F1 evaluation")
    
    return {
        'distribution': distribution,
        'total': total,
        'imbalance_flagged': is_imbalanced,
        'minority_pct': minority_pct,
        'majority_minority_ratio': ratio,
        'recommendation': 'Use stratified splits and class_weight=balanced' if is_imbalanced else 'No imbalance detected',
    }


def analyze_domains(df: pd.DataFrame) -> dict:
    """Analyze domain frequencies and cross-tabulation."""
    result = {}
    
    for col in ['resume_domain', 'jd_domain']:
        if col not in df.columns:
            result[col] = 'Not available'
            continue
        
        # Fill missing with 'Unspecified'
        domain_series = df[col].fillna('Unspecified')
        result[f'{col}_frequencies'] = domain_series.value_counts().head(20).to_dict()
        result[f'{col}_missing_rate'] = round(df[col].isna().sum() / len(df) * 100, 2)
    
    # Cross-tabulation if both domains present
    if 'resume_domain' in df.columns and 'jd_domain' in df.columns:
        df_copy = df.copy()
        df_copy['resume_domain'] = df_copy['resume_domain'].fillna('Unspecified')
        df_copy['jd_domain'] = df_copy['jd_domain'].fillna('Unspecified')
        try:
            cross_tab = pd.crosstab(df_copy['resume_domain'], df_copy['label'])
            result['domain_label_crosstab'] = cross_tab.head(10).to_dict()
        except Exception as e:
            logger.warning(f"Cross-tabulation failed: {e}")
    
    return result


def save_label_mapping():
    """Save label mapping to disk."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    mapping_path = CONFIG_DIR / "label_mapping.json"
    mapping_data = {
        'label_to_int': LABEL_MAPPING,
        'int_to_label': {str(k): v for k, v in INVERSE_LABEL_MAPPING.items()},
        'description': 'Fixed ordinal label mapping for CV-Job compatibility classification',
    }
    with open(mapping_path, 'w') as f:
        json.dump(mapping_data, f, indent=2)
    logger.info(f"Label mapping saved to: {mapping_path}")
    return mapping_path


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    sys.path.insert(0, str(Path(__file__).parent))
    try:
        from ml_pipeline.load_data import load_data
        from ml_pipeline.inspect_data import validate_and_rename_columns
        from ml_pipeline.clean_data import clean_dataset
    except (ImportError, ModuleNotFoundError):
        from load_data import load_data
        from inspect_data import validate_and_rename_columns
        from clean_data import clean_dataset
    from preprocessing import preprocess_dataframe
    
    df = load_data()
    df = validate_and_rename_columns(df)
    df, _ = clean_dataset(df)
    
    # Analyze
    label_analysis = analyze_label_distribution(df)
    domain_analysis = analyze_domains(df)
    
    # Encode labels
    df['label_encoded'] = encode_labels(df['label'])
    
    # Save mapping
    save_label_mapping()
    
    # Save report
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report = {'label_analysis': label_analysis, 'domain_analysis': domain_analysis}
    
    # Convert non-serializable values
    def make_serializable(obj):
        if isinstance(obj, (np.integer, np.int64)): return int(obj)
        if isinstance(obj, (np.floating, np.float64)): return float(obj)
        if isinstance(obj, dict): return {k: make_serializable(v) for k, v in obj.items()}
        if isinstance(obj, list): return [make_serializable(i) for i in obj]
        return obj
    
    with open(REPORTS_DIR / "label_analysis.json", 'w') as f:
        json.dump(make_serializable(report), f, indent=2)
    
    logger.info(f"Label distribution: {label_analysis['distribution']}")
    logger.info(f"Imbalance flagged: {label_analysis['imbalance_flagged']}")
