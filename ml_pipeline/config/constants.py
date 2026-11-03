"""
Global constants for ML pipeline.
"""
from pathlib import Path

# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
MODELS_DIR = PROJECT_ROOT / "models"
REPORTS_DIR = PROJECT_ROOT / "reports"

# Dataset
DATASET_NAME = "med2425/resume-job-fit-merged-v1"
REQUIRED_COLUMNS = ['resume', 'jd', 'label']
OPTIONAL_COLUMNS = ['resume_domain', 'jd_domain']

# Label mapping
LABEL_MAPPING = {'No Fit': 0, 'Potential Fit': 1, 'Good Fit': 2}
CLASS_NAMES = ['No Fit', 'Potential Fit', 'Good Fit']

# Preprocessing
MIN_TEXT_LENGTH = 15
MAX_TEXT_LENGTH = 50000

# Model
RANDOM_STATE = 42
TEST_SIZE = 0.2

# TF-IDF
TFIDF_MAX_FEATURES = 20000
TFIDF_NGRAM_RANGE = (1, 2)
TFIDF_MIN_DF = 2

# Scoring
SCORE_MIN = 0.0
SCORE_MAX = 100.0
