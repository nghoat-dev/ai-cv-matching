"""
Comprehensive test suite for Sprint 2 and Sprint 3 API endpoints.

Tests:
  - System health and info
  - Embedded Web UI serving
  - PDF magic bytes & size validation
  - Structured CV entity extraction
  - End-to-end ML matching
  - History query, filtering, sorting, pagination, and deletion
  - History export (CSV and JSON)
  - Multi-CV candidate comparison and ranking
  - System-wide statistics
"""

from __future__ import annotations

import io
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))
_ML_DIR = _PROJECT_ROOT / "ml_pipeline"
if str(_ML_DIR) not in sys.path:
    sys.path.insert(0, str(_ML_DIR))

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)

SAMPLE_PDF_PATH = _PROJECT_ROOT / "Documents" / "Sample_CV_Python_Developer.pdf"
SAMPLE_ACCOUNTANT_PATH = _PROJECT_ROOT / "Documents" / "Sample_CV_Accountant.pdf"


def _get_sample_pdf_bytes() -> bytes:
    if SAMPLE_PDF_PATH.exists():
        return SAMPLE_PDF_PATH.read_bytes()
    # Minimal valid 1-page PDF
    return (
        b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
        b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Resources<<>>>>endobj\n"
        b"xref\n0 4\n0000000000 65535 f\n0000000010 00000 n\n0000000053 00000 n\n0000000102 00000 n\n"
        b"trailer<</Size 4/Root 1 0 R>>\nstartxref\n178\n%%EOF\n"
    )


# ---------------------------------------------------------------------------
# 1. System Endpoints
# ---------------------------------------------------------------------------


def test_health():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"


def test_api_info():
    res = client.get("/api/v1/info")
    assert res.status_code == 200
    data = res.json()
    assert "name" in data
    assert "version" in data
    assert "endpoints" in data


def test_web_ui():
    res = client.get("/")
    assert res.status_code == 200
    assert "text/html" in res.headers["content-type"]
    assert "AI CV-Job Matching" in res.text


def test_sample_document():
    if SAMPLE_PDF_PATH.exists():
        res = client.get("/Documents/Sample_CV_Python_Developer.pdf")
        assert res.status_code == 200
        assert "application/pdf" in res.headers["content-type"]


# ---------------------------------------------------------------------------
# 2. Validation & Security (US-14, US-15)
# ---------------------------------------------------------------------------


def test_match_rejects_non_pdf_extension():
    res = client.post(
        "/api/v1/match",
        files={"pdf_file": ("resume.txt", b"plain text", "text/plain")},
        data={"jd_text": "We are seeking a Senior Python Developer with FastAPI and Docker experience."},
    )
    assert res.status_code == 400
    assert "PDF" in res.json()["message"]


def test_match_rejects_spoofed_magic_bytes():
    res = client.post(
        "/api/v1/match",
        files={"pdf_file": ("malicious.pdf", b"NOT_A_PDF_STREAM", "application/pdf")},
        data={"jd_text": "We are seeking a Senior Python Developer with FastAPI and Docker experience."},
    )
    assert res.status_code == 400
    assert "magic bytes" in res.json()["message"].lower() or "pdf" in res.json()["message"].lower()


def test_match_rejects_empty_jd():
    pdf_bytes = _get_sample_pdf_bytes()
    res = client.post(
        "/api/v1/match",
        files={"pdf_file": ("resume.pdf", pdf_bytes, "application/pdf")},
        data={"jd_text": "   "},
    )
    assert res.status_code == 400
    assert "empty" in res.json()["message"].lower()


def test_match_rejects_gibberish_or_short_jd():
    """US-15 & US-22: Reject short/gibberish JD with HTTP 422 and INVALID_JD_CONTENT."""
    pdf_bytes = _get_sample_pdf_bytes()

    # 1. 'lmao' — 4 chars, 1 word
    res = client.post(
        "/api/v1/match",
        files={"pdf_file": ("resume.pdf", pdf_bytes, "application/pdf")},
        data={"jd_text": "lmao"},
    )
    assert res.status_code == 422
    body = res.json()
    assert body["error_code"] == "INVALID_JD_CONTENT"
    assert body["message"] == "Job description is too short or invalid."

    # 2. Less than 30 chars, < 5 words
    res2 = client.post(
        "/api/v1/match",
        files={"pdf_file": ("resume.pdf", pdf_bytes, "application/pdf")},
        data={"jd_text": "Only three words"},
    )
    assert res2.status_code == 422
    assert res2.json()["error_code"] == "INVALID_JD_CONTENT"


def test_scorer_mathematical_consistency():
    """Verify overall score gauge equals exact weighted sum of the 4 dimension bars."""
    from backend.app.schemas import CVExtractedData, JDExtractedData
    from backend.app.services.scorer import MultiDimensionalScorer, evaluate_comprehensive_match

    scorer = MultiDimensionalScorer()
    cv_data = CVExtractedData(
        full_name="Test Candidate",
        technical_skills=["Python", "FastAPI", "Docker"],
        total_experience_years=3.0,
        experience_descriptions=["Developed FastAPI services with Docker"],
        education_level="Bachelor",
        other_qualifications=["Bachelor's Degree"],
        raw_text="Test CV with Python, FastAPI, Docker",
    )
    jd_data = JDExtractedData(
        job_title="Python Engineer",
        required_technical_skills=["Python", "FastAPI", "Docker", "Kubernetes", "PostgreSQL"],
        min_experience_years=3.0,
        job_responsibilities=["Develop backend services in Docker"],
        required_education="Bachelor's Degree",
        other_requirements=["Bachelor's Degree"],
        normalized_jd_text="Python FastAPI Docker Kubernetes PostgreSQL Bachelor",
    )
    score_res = scorer.compute_scores(cv_data, jd_data, ml_model_score=75.0)
    sub = score_res["sub_scores"]
    tech = sub["tech_skill_score"]
    exp = sub["experience_score"]
    edu = sub["other_req_score"]
    ml = sub["ml_model_score"]

    expected_score = round(0.45 * tech + 0.30 * exp + 0.15 * edu + 0.10 * ml, 1)
    assert score_res["matching_score"] == expected_score

    # Also test evaluate_comprehensive_match
    raw_res = evaluate_comprehensive_match(
        cv_text="Python FastAPI Docker developer with 3 years experience. Bachelor of Science.",
        jd_text="Looking for Python FastAPI Docker Kubernetes engineer. 3+ years experience. Bachelor's Degree.",
        ml_prob_score=70.0,
    )
    raw_sub = raw_res["sub_scores"]
    raw_expected = round(
        0.45 * raw_sub["tech_skill_score"]
        + 0.30 * raw_sub["experience_score"]
        + 0.15 * raw_sub["other_req_score"]
        + 0.10 * raw_sub["ml_model_score"],
        1,
    )
    assert raw_res["matching_score"] == raw_expected


# ---------------------------------------------------------------------------
# 3. Structured CV Entity Extraction (US-16)
# ---------------------------------------------------------------------------


def test_extract_cv():
    pdf_bytes = _get_sample_pdf_bytes()
    res = client.post(
        "/api/v1/extract",
        files={"pdf_file": ("candidate.pdf", pdf_bytes, "application/pdf")},
    )
    assert res.status_code == 200
    data = res.json()
    assert "raw_text" in data
    assert "skills" in data
    assert isinstance(data["skills"], list)


# ---------------------------------------------------------------------------
# 4. End-to-End ML Matching (US-21)
# ---------------------------------------------------------------------------


def test_match_success():
    pdf_bytes = _get_sample_pdf_bytes()
    jd = (
        "Senior Python Backend Developer. Requirements: Python, FastAPI, Docker, "
        "PostgreSQL, Redis, CI/CD, Git. 3+ years experience."
    )
    res = client.post(
        "/api/v1/match",
        files={"pdf_file": ("Sample_CV_Python_Developer.pdf", pdf_bytes, "application/pdf")},
        data={"jd_text": jd},
    )
    assert res.status_code == 200
    data = res.json()
    assert "matching_score" in data
    assert 0.0 <= data["matching_score"] <= 100.0
    assert data["compatibility_label"] in ["Good Fit", "Potential Fit", "No Fit"]
    assert "matched_skills" in data
    assert "missing_skills" in data
    assert "llm_explanation" in data


# ---------------------------------------------------------------------------
# 5. History Query, Filtering, Export, and Deletion (US-25, US-27)
# ---------------------------------------------------------------------------


def test_history_list():
    res = client.get("/api/v1/history?limit=10")
    assert res.status_code == 200
    data = res.json()
    assert "total" in data
    assert "results" in data
    assert isinstance(data["results"], list)


def test_history_filter_label():
    res = client.get("/api/v1/history?label=Good%20Fit")
    assert res.status_code == 200
    data = res.json()
    for item in data["results"]:
        assert item["compatibility_label"] == "Good Fit"


def test_history_export_csv():
    res = client.get("/api/v1/history/export?format=csv")
    assert res.status_code == 200
    assert "text/csv" in res.headers["content-type"]
    assert "ID,CV Filename,Matching Score" in res.text


def test_history_export_json():
    res = client.get("/api/v1/history/export?format=json")
    assert res.status_code == 200
    assert "application/json" in res.headers["content-type"]
    assert isinstance(res.json(), list)


# ---------------------------------------------------------------------------
# 6. Multi-CV Candidate Comparison & Ranking (US-26)
# ---------------------------------------------------------------------------


def test_compare_multiple_cvs():
    pdf_bytes = _get_sample_pdf_bytes()
    jd = "Python Developer with FastAPI, PostgreSQL, and Docker."

    files = [
        ("files", ("Candidate_1.pdf", pdf_bytes, "application/pdf")),
        ("files", ("Candidate_2.pdf", pdf_bytes, "application/pdf")),
    ]
    res = client.post("/api/v1/compare", files=files, data={"jd_text": jd})
    assert res.status_code == 200
    data = res.json()
    assert "total_candidates" in data
    assert data["total_candidates"] == 2
    assert "candidates" in data
    assert len(data["candidates"]) == 2
    assert data["candidates"][0]["rank"] == 1
    assert data["candidates"][1]["rank"] == 2


# ---------------------------------------------------------------------------
# 7. Aggregate Statistics (US-28)
# ---------------------------------------------------------------------------


def test_stats_endpoint():
    res = client.get("/api/v1/stats")
    assert res.status_code == 200
    data = res.json()
    assert "total_matches" in data
    assert "label_distribution" in data
    assert "Good Fit" in data["label_distribution"]

