"""
Sprint 1 ML Pipeline Unit Tests covering all Acceptance Criteria edge cases.
"""
import sys
import json
import numpy as np
import pandas as pd
import pytest
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "ml_pipeline"))

from inspect_data import validate_and_rename_columns, SchemaValidationError
from clean_data import clean_dataset
from preprocessing import normalize_text
from analyze_labels import encode_labels, decode_labels, LABEL_MAPPING, INVERSE_LABEL_MAPPING
from feature_extraction import FeatureExtractor, compute_pairwise_features
from train_baseline import compute_matching_score
from evaluate_baseline import evaluate_predictions


def test_schema_validation_missing_core_column():
    """US-06 Edge Case: Missing required column raises SchemaValidationError."""
    mock_df = pd.DataFrame({
        'resume': ['Sample resume text for testing.'],
        'label': ['Good Fit'],
    })
    with pytest.raises(SchemaValidationError) as exc_info:
        validate_and_rename_columns(mock_df)
    assert 'Missing required column' in str(exc_info.value)


def test_synthetic_dirty_data_cleaning():
    """
    US-07 Edge Case:
    Synthetic 6-row DataFrame:
    - Row 0: Valid row
    - Row 1: Null resume
    - Row 2: Whitespace-only JD
    - Row 3: Invalid label 'Unknown'
    - Row 4: Duplicate of row 0
    - Row 5: Another valid unique row
    Expected: exactly 2 valid unique rows remain.
    """
    dirty_df = pd.DataFrame([
        {'resume': 'Software engineer with 5 years experience in Python and SQL.', 'jd': 'Seeking Python engineer with strong database knowledge.', 'label': 'Good Fit'},
        {'resume': None, 'jd': 'Looking for Python developer.', 'label': 'Potential Fit'},
        {'resume': 'Experienced frontend developer React and JavaScript.', 'jd': '   \n\t  ', 'label': 'No Fit'},
        {'resume': 'Data scientist with machine learning and deep learning skills.', 'jd': 'Looking for ML engineer.', 'label': 'Unknown'},
        {'resume': 'Software engineer with 5 years experience in Python and SQL.', 'jd': 'Seeking Python engineer with strong database knowledge.', 'label': 'Good Fit'},
        {'resume': 'DevOps specialist with Docker, Kubernetes, CI/CD experience.', 'jd': 'Looking for cloud engineer to manage AWS infrastructure.', 'label': 'Good Fit'},
    ])
    
    cleaned_df, audit = clean_dataset(dirty_df)
    assert len(cleaned_df) == 2, f"Expected 2 rows, got {len(cleaned_df)}"
    assert audit['dropped_null_resume'] == 1
    assert audit['dropped_empty_short_jd'] == 1
    assert audit['dropped_invalid_label'] == 1
    assert audit['dropped_exact_duplicates'] == 1


def test_clean_dataset_idempotency():
    """US-07 Edge Case: Cleaning an already-cleaned DataFrame drops 0 rows."""
    valid_df = pd.DataFrame([
        {'resume': 'Senior Java developer with Spring Boot experience.', 'jd': 'Java engineer position.', 'label': 'Good Fit'},
        {'resume': 'Product manager with agile and scrum certification.', 'jd': 'PM role in tech startup.', 'label': 'Potential Fit'},
    ])
    
    clean1, _ = clean_dataset(valid_df)
    clean2, audit2 = clean_dataset(clean1)
    
    assert len(clean1) == len(clean2)
    assert audit2['final_count'] == len(clean1)


def test_technical_token_preservation():
    """US-08 Edge Case: Preserve technical skill tokens intact."""
    raw = "Senior Developer: C++, C#, .NET Core, Node.js & CI/CD!\n\nExperience: 5+ yrs"
    normalized = normalize_text(raw)
    
    expected_tokens = ['c++', 'c#', '.net', 'node.js', 'ci/cd']
    for token in expected_tokens:
        assert token in normalized, f"Expected token '{token}' in '{normalized}'"


def test_word_boundary_html_stripping():
    """US-08 Edge Case: Word boundary safety when stripping HTML tags."""
    raw = "<p>Python</p><p>Developer</p>"
    normalized = normalize_text(raw)
    assert "python developer" in normalized
    assert "pythondeveloper" not in normalized


def test_label_mapping_round_trip():
    """US-09 Edge Case: Bidirectional label mapping round-trip."""
    original = pd.Series(['No Fit', 'Potential Fit', 'Good Fit'])
    encoded = encode_labels(original)
    assert list(encoded) == [0, 1, 2]
    
    decoded = decode_labels(encoded)
    assert list(decoded) == ['No Fit', 'Potential Fit', 'Good Fit']


def test_label_encoder_invalid_value_raises():
    """US-09: Invalid label raises ValueError."""
    with pytest.raises(ValueError) as exc:
        encode_labels(pd.Series(['Super Fit']))
    assert 'Invalid label value' in str(exc.value)


def test_all_oov_zero_division_guard():
    """US-11 Edge Case: Out-of-vocabulary pair produces finite 0.0 without NaN/division-by-zero."""
    extractor = FeatureExtractor()
    train_resumes = [
        "python django backend developer software engineer",
        "python flask backend developer software engineer",
    ]
    train_jds = [
        "seeking python backend developer software engineer",
        "seeking python backend developer software engineer",
    ]
    extractor.fit(train_resumes, train_jds)
    
    oov_resume = ["zzzz qqqq xxxx"]
    oov_jd = ["aaaa bbbb cccc"]
    X = extractor.transform(oov_resume, oov_jd)
    
    assert not np.isnan(X.data).any() if hasattr(X, 'data') else not np.isnan(X).any()
    assert not np.isinf(X.data).any() if hasattr(X, 'data') else not np.isinf(X).any()


def test_scoring_formula_monotonicity():
    """US-12 Edge Case: Monotonicity of matching score."""
    probs_a = np.array([[0.05, 0.10, 0.85]])  # High Good Fit
    probs_b = np.array([[0.75, 0.10, 0.15]])  # High No Fit
    
    score_a = compute_matching_score(probs_a, np.array([0.9]))[0]
    score_b = compute_matching_score(probs_b, np.array([0.2]))[0]
    
    assert score_a > score_b, f"Score A ({score_a}) must be > Score B ({score_b})"
    assert 0.0 <= score_a <= 100.0
    assert 0.0 <= score_b <= 100.0


def test_zero_division_evaluation_resilience():
    """US-13 Edge Case: Unpredicted class evaluates cleanly to 0.0 without NaN."""
    y_true = np.array([0, 0, 1, 1, 2, 2])
    y_pred = np.array([0, 0, 0, 0, 2, 2])  # Class 1 never predicted
    
    metrics = evaluate_predictions(y_true, y_pred)
    assert metrics['per_class']['Potential Fit']['precision'] == 0.0
    assert metrics['per_class']['Potential Fit']['f1'] == 0.0
    assert not np.isnan(metrics['macro_f1'])


if __name__ == "__main__":
    test_schema_validation_missing_core_column()
    test_synthetic_dirty_data_cleaning()
    test_clean_dataset_idempotency()
    test_technical_token_preservation()
    test_word_boundary_html_stripping()
    test_label_mapping_round_trip()
    test_label_encoder_invalid_value_raises()
    test_all_oov_zero_division_guard()
    test_scoring_formula_monotonicity()
    test_zero_division_evaluation_resilience()
    print("ALL ML PIPELINE UNIT TESTS PASSED!")
