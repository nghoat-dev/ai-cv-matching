"""
Sprint 1 API integration and contract tests.
"""
import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.main import app
from backend.app.schemas import (
    CVUploadRequest,
    CVExtractionResult,
    JDProcessingResult,
    MatchingResponse,
    ErrorResponse,
)

client = TestClient(app)

MINIMAL_VALID_PDF = (
    b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
    b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
    b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Resources<<>>>>endobj\n"
    b"xref\n0 4\n0000000000 65535 f\n0000000010 00000 n\n0000000053 00000 n\n0000000102 00000 n\n"
    b"trailer<</Size 4/Root 1 0 R>>\nstartxref\n178\n%%EOF\n"
)


def test_health():
    """US-03 & INT-01: Health check endpoint returns 200 and healthy status."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_api_info():
    """US-03: API info endpoint returns 200 and endpoint list."""
    response = client.get("/api/v1/info")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "endpoints" in data


def test_match_valid_input():
    """US-01 & US-03: Valid CV PDF and non-empty JD returns MatchingResponse schema."""
    pdf_content = MINIMAL_VALID_PDF
    response = client.post(
        "/api/v1/match",
        files={"pdf_file": ("resume.pdf", pdf_content, "application/pdf")},
        data={"jd_text": "Looking for Senior Python Developer with FastAPI experience."},
    )
    assert response.status_code == 200
    data = response.json()
    assert 0.0 <= data["matching_score"] <= 100.0
    assert data["compatibility_label"] in ["Good Fit", "Potential Fit", "No Fit"]
    assert isinstance(data["matched_skills"], list)
    assert isinstance(data["missing_skills"], list)
    assert data["llm_status"] in ["success", "fallback"]


def test_match_invalid_file_extension():
    """US01-AC05: Unsupported file format (.docx) rejected with 400 and INVALID_INPUT."""
    response = client.post(
        "/api/v1/match",
        files={"pdf_file": ("resume.docx", b"docx data", "application/vnd.openxmlformats")},
        data={"jd_text": "Python Developer"},
    )
    assert response.status_code == 400
    body = response.json()
    assert body["error_code"] == "INVALID_INPUT"


def test_match_empty_jd():
    """US01-AC05: Whitespace-only JD rejected with 400 and INVALID_INPUT."""
    response = client.post(
        "/api/v1/match",
        files={"pdf_file": ("resume.pdf", b"%PDF-1.4 mock", "application/pdf")},
        data={"jd_text": "   \n\t  "},
    )
    assert response.status_code == 400
    body = response.json()
    assert body["error_code"] == "INVALID_INPUT"


def test_schema_extra_fields_forbidden():
    """US01-AC07: Schemas forbid extra unauthorized fields."""
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        MatchingResponse(
            matching_score=80.0,
            compatibility_label="Good Fit",
            matched_skills=["Python"],
            missing_skills=[],
            llm_explanation="Great fit",
            llm_status="success",
            extra_field="malicious_payload",
        )


def test_score_boundary_validation():
    """US01 Edge case: Boundary score validation (0 <= score <= 100)."""
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        MatchingResponse(
            matching_score=150.0,
            compatibility_label="Good Fit",
            llm_status="success",
        )

    with pytest.raises(ValidationError):
        MatchingResponse(
            matching_score=-10.0,
            compatibility_label="No Fit",
            llm_status="fallback",
        )


def test_llm_fallback_mode():
    """US-04 & US01-AC06: LLM fallback gracefully preserves ML score."""
    from backend.app.services.llm_service import LLMService

    service = LLMService()
    service.api_key = ""  # Force fallback test
    # Without real API key, must return fallback
    result = service.generate_explanation("Python CV", "Python JD", 85.0)
    assert result["status"] == "fallback"
    assert "LLM service unavailable" in result["explanation"]


if __name__ == "__main__":
    test_health()
    test_api_info()
    test_match_valid_input()
    test_match_invalid_file_extension()
    test_match_empty_jd()
    test_schema_extra_fields_forbidden()
    test_score_boundary_validation()
    test_llm_fallback_mode()
    print("ALL API AND CONTRACT TESTS PASSED!")

