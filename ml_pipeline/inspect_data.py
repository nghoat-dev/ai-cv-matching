"""
US-06: Inspect and Validate Dataset Schema, Expected Fields, and License.
"""
import logging
import json
import pandas as pd
import numpy as np
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = ['resume', 'jd', 'label']
OPTIONAL_COLUMNS = ['resume_domain', 'jd_domain']
EXPECTED_COLUMNS = REQUIRED_COLUMNS + OPTIONAL_COLUMNS

COLUMN_ALIASES = {
    'job_description': 'jd',
    'cv': 'resume',
    'fit_label': 'label',
    'match_label': 'label',
}

REPORTS_DIR = Path(__file__).parent.parent / "reports"

class SchemaValidationError(Exception):
    pass

def validate_and_rename_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Validate schema and apply column renaming if needed."""
    df = df.copy()
    # Apply aliases
    rename_map = {}
    for alias, target in COLUMN_ALIASES.items():
        if alias in df.columns and target not in df.columns:
            rename_map[alias] = target
    if rename_map:
        logger.info(f"Renaming columns: {rename_map}")
        df = df.rename(columns=rename_map)
    
    # Check required columns
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise SchemaValidationError(f"Missing required column(s): {', '.join(missing)}")
    
    # Check optional
    for col in OPTIONAL_COLUMNS:
        if col not in df.columns:
            logger.warning(f"Optional column '{col}' not found.")
    
    return df

def profile_text_lengths(df: pd.DataFrame, columns: list) -> dict:
    """Compute text length statistics."""
    stats = {}
    for col in columns:
        if col not in df.columns:
            continue
        text_series = df[col].dropna().astype(str)
        char_lengths = text_series.str.len()
        word_counts = text_series.str.split().str.len()
        stats[col] = {
            'char_count': {
                'min': int(char_lengths.min()),
                'max': int(char_lengths.max()),
                'mean': round(float(char_lengths.mean()), 2),
                'median': round(float(char_lengths.median()), 2),
                'p5': round(float(char_lengths.quantile(0.05)), 2),
                'p95': round(float(char_lengths.quantile(0.95)), 2),
            },
            'word_count': {
                'min': int(word_counts.min()),
                'max': int(word_counts.max()),
                'mean': round(float(word_counts.mean()), 2),
                'median': round(float(word_counts.median()), 2),
            },
        }
        # Flag extreme outliers
        extreme_short = int((char_lengths < 10).sum())
        extreme_long = int((char_lengths > 50000).sum())
        stats[col]['extreme_outliers'] = {'too_short_lt10': extreme_short, 'too_long_gt50000': extreme_long}
        if extreme_short > 0:
            logger.warning(f"Column '{col}': {extreme_short} records with < 10 chars")
        if extreme_long > 0:
            logger.warning(f"Column '{col}': {extreme_long} records with > 50,000 chars")
    return stats

def check_non_string_entries(df: pd.DataFrame, columns: list) -> dict:
    """Check for non-string data types in text columns."""
    results = {}
    for col in columns:
        if col not in df.columns:
            continue
        non_string_count = int((~df[col].apply(lambda x: isinstance(x, str))).sum())
        results[col] = non_string_count
        if non_string_count > 0:
            logger.warning(f"Column '{col}': {non_string_count} non-string entries found")
    return results

def inspect_dataset(df: pd.DataFrame) -> dict:
    """Full inspection report."""
    report = {}
    
    # Schema
    report['schema'] = {
        'total_rows': len(df),
        'columns': list(df.columns),
        'dtypes': {k: str(v) for k, v in df.dtypes.items()},
        'null_counts': df.isnull().sum().to_dict(),
    }
    
    # Text statistics
    report['text_length_stats'] = profile_text_lengths(df, ['resume', 'jd'])
    
    # Non-string entries
    report['non_string_counts'] = check_non_string_entries(df, ['resume', 'jd', 'label'])
    
    # Label distribution
    if 'label' in df.columns:
        label_counts = df['label'].value_counts().to_dict()
        report['label_distribution'] = label_counts
    
    # Domain analysis
    for col in ['resume_domain', 'jd_domain']:
        if col in df.columns:
            report[f'{col}_top20'] = df[col].value_counts().head(20).to_dict()
    
    # Dataset info
    report['dataset_info'] = {
        'name': 'med2425/resume-job-fit-merged-v1',
        'platform': 'Hugging Face',
        'url': 'https://huggingface.co/datasets/med2425/resume-job-fit-merged-v1',
        'license': 'See dataset card on Hugging Face',
        'academic_use': True,
    }
    
    return report

if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    sys.path.insert(0, str(Path(__file__).parent))
    try:
        from ml_pipeline.load_data import load_data
    except (ImportError, ModuleNotFoundError):
        from load_data import load_data
    
    df = load_data()
    df = validate_and_rename_columns(df)
    
    report = inspect_dataset(df)
    
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORTS_DIR / "dataset_inspection.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, default=str)
    
    logger.info(f"Inspection report saved to: {report_path}")
    logger.info(f"Total rows: {report['schema']['total_rows']}")
    logger.info(f"Columns: {report['schema']['columns']}")
    logger.info(f"Label distribution: {report.get('label_distribution', 'N/A')}")
