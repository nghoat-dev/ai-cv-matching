"""
Test suite verifying US-15, US-22 input validation and mathematical score consistency.
"""
import sys
from pathlib import Path
_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import pytest
from fastapi.exceptions import HTTPException

from backend.app.main import _validate_jd_text
from backend.app.schemas import CVExtractedData, JDExtractedData
from backend.app.services.scorer import MultiDimensionalScorer, evaluate_comprehensive_match


def test_validate_jd_empty():
    """Empty or whitespace-only JD raises HTTP 400."""
    with pytest.raises(HTTPException) as exc_info:
        _validate_jd_text("")
    assert exc_info.value.status_code == 400

    with pytest.raises(HTTPException) as exc_info2:
        _validate_jd_text("   \n\t  ")
    assert exc_info2.value.status_code == 400


def test_validate_jd_lmao_returns_422():
    """Gibberish 'lmao' (<30 chars, <5 words) raises HTTP 422 with INVALID_JD_CONTENT."""
    with pytest.raises(HTTPException) as exc_info:
        _validate_jd_text("lmao")
    assert exc_info.value.status_code == 422
    assert exc_info.value.detail.get("error_code") == "INVALID_JD_CONTENT"
    assert exc_info.value.detail.get("message") == "Job description is too short or invalid."


def test_validate_jd_too_few_words_returns_422():
    """JD with < 5 words raises HTTP 422 with INVALID_JD_CONTENT even if length >= 30."""
    with pytest.raises(HTTPException) as exc_info:
        _validate_jd_text("1234567890 1234567890 1234567890 12345")
    assert exc_info.value.status_code == 422
    assert exc_info.value.detail.get("error_code") == "INVALID_JD_CONTENT"


def test_validate_jd_valid_passes():
    """Valid JD with >= 30 chars and >= 5 words passes validation."""
    valid_text = "We are seeking a Senior Python Developer with FastAPI and Docker experience."
    result = _validate_jd_text(valid_text)
    assert result == valid_text


def test_mathematical_score_consistency():
    """Verify matching_score equals exact round(0.45*tech + 0.30*exp + 0.15*edu + 0.10*ml, 1)."""
    scorer = MultiDimensionalScorer()
    cv_data = CVExtractedData(
        full_name="Jane Doe",
        technical_skills=["Python", "FastAPI", "Docker", "PostgreSQL"],
        total_experience_years=4.0,
        experience_descriptions=["Designed high-throughput FastAPI services with Docker"],
        education_level="Bachelor",
        other_qualifications=["Bachelor's Degree"],
        raw_text="Jane Doe, Python FastAPI Docker PostgreSQL developer",
    )
    jd_data = JDExtractedData(
        job_title="Backend Engineer",
        required_technical_skills=["Python", "FastAPI", "Docker", "Redis", "Kubernetes"],
        min_experience_years=3.0,
        job_responsibilities=["Develop backend APIs"],
        required_education="Bachelor's Degree",
        other_requirements=["Bachelor's Degree"],
        normalized_jd_text="Python FastAPI Docker Redis Kubernetes",
    )
    res = scorer.compute_scores(cv_data, jd_data, ml_model_score=78.5)
    sub = res["sub_scores"]
    tech = sub["tech_skill_score"]
    exp = sub["experience_score"]
    edu = sub["other_req_score"]
    ml = sub["ml_model_score"]

    expected_score = round(0.45 * tech + 0.30 * exp + 0.15 * edu + 0.10 * ml, 1)
    assert res["matching_score"] == expected_score

    # Also test evaluate_comprehensive_match
    comp_res = evaluate_comprehensive_match(
        cv_text="Python FastAPI developer with 4 years experience. Bachelor's Degree.",
        jd_text="Senior Python FastAPI Docker engineer with 3+ years experience. Bachelor's Degree.",
        ml_prob_score=72.0,
    )
    comp_sub = comp_res["sub_scores"]
    expected_comp = round(
        0.45 * comp_sub["tech_skill_score"]
        + 0.30 * comp_sub["experience_score"]
        + 0.15 * comp_sub["other_req_score"]
        + 0.10 * comp_sub["ml_model_score"],
        1,
    )
    assert comp_res["matching_score"] == expected_comp


if __name__ == "__main__":
    test_validate_jd_empty()
    test_validate_jd_lmao_returns_422()
    test_validate_jd_too_few_words_returns_422()
    test_validate_jd_valid_passes()
    test_mathematical_score_consistency()
    print("All validation & mathematical score consistency tests passed successfully!")
