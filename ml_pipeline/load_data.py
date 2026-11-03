"""
US-05: Download, Cache, and Load Primary Dataset from Hugging Face.

Dataset: med2425/resume-job-fit-merged-v1
"""
import os
import sys
import argparse
import logging
import hashlib
import pandas as pd
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

RAW_DATA_DIR = Path(__file__).parent.parent / "data" / "raw"
DATASET_NAME = "med2425/resume-job-fit-merged-v1"
CACHE_FILE = RAW_DATA_DIR / "dataset_cache.parquet"

def load_dataset_from_huggingface() -> pd.DataFrame:
    """Download dataset from Hugging Face and return as DataFrame."""
    from datasets import load_dataset
    logger.info(f"Downloading dataset: {DATASET_NAME}")
    ds = load_dataset(DATASET_NAME)
    # Combine all splits
    dfs = []
    for split_name, split_data in ds.items():
        df = split_data.to_pandas()
        df['_split'] = split_name
        dfs.append(df)
    df = pd.concat(dfs, ignore_index=True)
    logger.info(f"Downloaded dataset shape: {df.shape}")
    return df

def save_cache(df: pd.DataFrame) -> None:
    """Save DataFrame to local cache."""
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    df.to_parquet(CACHE_FILE, index=False)
    logger.info(f"Dataset cached to: {CACHE_FILE}")

def load_cache() -> pd.DataFrame:
    """Load DataFrame from local cache."""
    logger.info(f"Loading from local cache: {CACHE_FILE}")
    df = pd.read_parquet(CACHE_FILE)
    logger.info(f"Loaded from cache. Shape: {df.shape}, Memory: {df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")
    return df

def is_cache_valid() -> bool:
    """Check if local cache exists and is non-empty."""
    if not CACHE_FILE.exists():
        return False
    if CACHE_FILE.stat().st_size == 0:
        logger.warning("Cache file is empty/zero-byte. Will re-download.")
        return False
    try:
        df = pd.read_parquet(CACHE_FILE)
        return len(df) > 0
    except Exception as e:
        logger.warning(f"Cache file corrupted: {e}. Will re-download.")
        return False

def load_data(force_download: bool = False) -> pd.DataFrame:
    """
    Main function to load the dataset.
    
    Args:
        force_download: If True, bypass local cache and re-download.
    
    Returns:
        DataFrame with the dataset.
    """
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    if not force_download and is_cache_valid():
        return load_cache()
    
    if force_download:
        logger.info("Force download requested. Bypassing cache.")
    
    try:
        df = load_dataset_from_huggingface()
        save_cache(df)
        return df
    except Exception as e:
        if not force_download and is_cache_valid():
            logger.warning(f"Download failed: {e}. Falling back to cache.")
            return load_cache()
        logger.error(f"Network unreachable and no local cache found at {RAW_DATA_DIR}")
        logger.error(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Load dataset from Hugging Face")
    parser.add_argument("--force-download", action="store_true", help="Force re-download bypassing cache")
    args = parser.parse_args()
    
    df = load_data(force_download=args.force_download)
    logger.info(f"Dataset loaded successfully. Shape: {df.shape}")
    logger.info(f"Columns: {list(df.columns)}")
    assert len(df) > 0, "Dataset is empty!"
    logger.info("✓ Dataset validation passed.")
