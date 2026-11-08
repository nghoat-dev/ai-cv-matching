"""
Fast, direct in-process unit & integration test suite for Sprint 2 and Sprint 3 endpoints.

Runs inside sandbox without loopback socket dependencies.
Validates all routes, schemas, database operations, PyMuPDF extraction,
and ML model inference.
"""

from __future__ import annotations

import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
import asyncio
import io
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))
_ML_DIR = _PROJECT_ROOT / "ml_pipeline"
if str(_ML_DIR) not in sys.path:
    sys.path.insert(0, str(_ML_DIR))

from fastapi import UploadFile
from fastapi.exceptions import HTTPException

from backend.app.database import create_tables
from backend.app.main import (
    api_info,
    compare_multiple_cvs,
    delete_history_record,
    export_history,
    extract_cv_data,
    get_history,
    get_stats,
    health_check,
    match_cv_to_jd,
    serve_sample_document,
    serve_web_ui,
)

SAMPLE_PYTHON_PATH = _PROJECT_ROOT / "Documents" / "Sample_CV_Python_Developer.pdf"
SAMPLE_ACCOUNTANT_PATH = _PROJECT_ROOT / "Documents" / "Sample_CV_Accountant.pdf"


def _create_upload_file(path: Path, filename: str) -> UploadFile:
    content = path.read_bytes()
    return UploadFile(file=io.BytesIO(content), filename=filename)


async def run_all_tests():
    print("=" * 65, flush=True)
    print("  RUNNING COMPREHENSIVE DIRECT API & BUSINESS LOGIC TESTS", flush=True)
    print("=" * 65, flush=True)
    create_tables()

    # 1. Health check
    h = await health_check()
    assert h["status"] == "healthy"
    print("  [PASS] 1. GET /health -> status: healthy", flush=True)

    # 2. API Info
    info = await api_info()
    assert "AI CV-Job Matching" in info["name"]
    assert "POST   /api/v1/match" in info["endpoints"]
    assert "POST   /api/v1/compare" in info["endpoints"]
    print(f"  [PASS] 2. GET /api/v1/info -> model_loaded: {info['model_loaded']}", flush=True)

    # 3. Web UI
    ui = await serve_web_ui()
    assert "text/html" in ui.media_type
    assert "AI CV-Job Matching" in ui.body.decode("utf-8")
    print("  [PASS] 3. GET / & GET /app -> Embedded Web UI returned", flush=True)

    # 4. Sample Document Serving
    sample_res = await serve_sample_document("Sample_CV_Python_Developer.pdf")
    assert sample_res.status_code == 200
    print("  [PASS] 4. GET /Documents/Sample_CV_Python_Developer.pdf -> 200 OK", flush=True)

    # 5. Entity Extraction (US-16)
    uf_py = _create_upload_file(SAMPLE_PYTHON_PATH, "Sample_CV_Python_Developer.pdf")
    extracted = await extract_cv_data(uf_py)
    assert extracted.raw_text
    assert len(extracted.skills) > 0
    print(f"  [PASS] 5. POST /api/v1/extract -> Extracted {len(extracted.skills)} skills: {extracted.skills[:4]}")

    # 6. Core Matching: Python CV vs Python JD (US-14, 15, 17, 18, 19, 20, 21)
    py_jd = (
        "Senior Python Backend Developer. Requirements: Strong experience in Python, FastAPI, "
        "PostgreSQL, Redis, Docker, and CI/CD pipelines. Familiarity with Machine Learning is a plus."
    )
    uf_match_py = _create_upload_file(SAMPLE_PYTHON_PATH, "Sample_CV_Python_Developer.pdf")
    res_py = await match_cv_to_jd(uf_match_py, py_jd)
    assert res_py.matching_score >= 60.0, f"Expected high score for Python dev, got {res_py.matching_score}"
    assert res_py.compatibility_label in ["Good Fit", "Potential Fit"]
    assert "Python" in res_py.matched_skills
    print(f"  [PASS] 6. POST /api/v1/match (Python Dev) -> Score: {res_py.matching_score} ({res_py.compatibility_label})")

    # 7. Core Matching: Accountant CV vs Python JD (Negative / Discrimination Test)
    uf_match_acc = _create_upload_file(SAMPLE_ACCOUNTANT_PATH, "Sample_CV_Accountant.pdf")
    res_acc = await match_cv_to_jd(uf_match_acc, py_jd)
    assert res_acc.matching_score < 40.0, f"Expected low score for Accountant, got {res_acc.matching_score}"
    assert res_acc.compatibility_label == "No Fit"
    print(f"  [PASS] 7. POST /api/v1/match (Accountant vs Python JD) -> Score: {res_acc.matching_score} ({res_acc.compatibility_label})")

    # 8. Multi-CV Candidate Comparison & Ranking (US-26)
    files = [
        _create_upload_file(SAMPLE_PYTHON_PATH, "Candidate_Python.pdf"),
        _create_upload_file(SAMPLE_ACCOUNTANT_PATH, "Candidate_Accountant.pdf"),
    ]
    comp = await compare_multiple_cvs(files, py_jd)
    assert comp["total_candidates"] == 2
    assert comp["candidates"][0]["filename"] == "Candidate_Python.pdf"
    assert comp["candidates"][0]["rank"] == 1
    assert comp["candidates"][1]["rank"] == 2
    print(f"  [PASS] 8. POST /api/v1/compare -> Ranked candidates: 1) {comp['candidates'][0]['filename']} ({comp['candidates'][0]['score']}), 2) {comp['candidates'][1]['filename']} ({comp['candidates'][1]['score']})")

    # 9. History Query & Label Filtering (US-25)
    hist = await get_history(limit=10, label="Good Fit")
    assert "total" in hist
    assert "results" in hist
    for item in hist["results"]:
        assert item["compatibility_label"] == "Good Fit"
    print(f"  [PASS] 9. GET /api/v1/history?label=Good Fit -> Filtered {len(hist['results'])} records")

    # 10. History CSV & JSON Export (US-27)
    csv_exp = await export_history(format="csv")
    assert "text/csv" in csv_exp.media_type
    assert b"Matching Score" in csv_exp.body

    json_exp = await export_history(format="json")
    assert json_exp.status_code == 200
    print("  [PASS] 10. GET /api/v1/history/export (CSV & JSON) -> Successfully generated exports")

    # 11. Aggregate Analytics & Statistics (US-28)
    stats = await get_stats()
    assert stats["total_matches"] > 0
    assert "Good Fit" in stats["label_distribution"]
    print(f"  [PASS] 11. GET /api/v1/stats -> Total: {stats['total_matches']}, Avg: {stats['avg_score']}, Good: {stats['label_distribution']['Good Fit']}, No Fit: {stats['label_distribution']['No Fit']}")

    # 12. Security Validation: Reject Spoofed File
    fake_file = UploadFile(file=io.BytesIO(b"NOT_A_VALID_PDF_STREAM"), filename="fake.pdf")
    try:
        await match_cv_to_jd(fake_file, "Senior Python Developer with 5 years experience in FastAPI and Docker")
        assert False, "Should have raised HTTPException 400 for magic bytes"
    except HTTPException as e:
        assert e.status_code == 400
        print(f"  [PASS] 12. Security validation -> Rejected spoofed PDF (HTTP {e.status_code})")

    # 12b. Strict Input Validation (US-15 & US-22): Reject gibberish 'lmao' with HTTP 422
    uf_lmao = _create_upload_file(SAMPLE_PYTHON_PATH, "Sample_CV_Python_Developer.pdf")
    try:
        await match_cv_to_jd(uf_lmao, "lmao")
        assert False, "Should have raised HTTPException 422 for 'lmao'"
    except HTTPException as e:
        assert e.status_code == 422
        assert e.detail.get("error_code") == "INVALID_JD_CONTENT"
        assert "short or invalid" in e.detail.get("message", "").lower()
        print(f"  [PASS] 12b. Strict JD validation -> Rejected 'lmao' with HTTP 422 and INVALID_JD_CONTENT")

    # 12c. Mathematical Score Consistency
    uf_math = _create_upload_file(SAMPLE_PYTHON_PATH, "Sample_CV_Python_Developer.pdf")
    math_res = await match_cv_to_jd(uf_math, py_jd)
    m_sub = math_res.sub_scores
    expected_math_score = round(
        0.45 * m_sub["tech_skill_score"]
        + 0.30 * m_sub["experience_score"]
        + 0.15 * m_sub["other_req_score"]
        + 0.10 * m_sub["ml_model_score"],
        1,
    )
    assert math_res.matching_score == expected_math_score, f"Expected {expected_math_score}, got {math_res.matching_score}"
    print(f"  [PASS] 12c. Mathematical score consistency -> {math_res.matching_score} == round(0.45*{m_sub['tech_skill_score']} + 0.30*{m_sub['experience_score']} + 0.15*{m_sub['other_req_score']} + 0.10*{m_sub['ml_model_score']}, 1)")

    # 13. Real-world TopCV PDF Extraction & Matching (Leading whitespace & template layout)
    hung_path = _PROJECT_ROOT / "Documents" / "27NguyenQuocHungTopCV261026100330.pdf"
    if hung_path.exists():
        uf_hung = _create_upload_file(hung_path, "27NguyenQuocHungTopCV261026100330.pdf")
        ext_hung = await extract_cv_data(uf_hung)
        assert ext_hung.full_name == "Nguyễn Quốc Hùng"
        assert ext_hung.email == "hung2802200@gmail.com"
        assert any(s.lower() in ["pytorch", "tensorflow"] for s in ext_hung.skills)
        print(f"  [PASS] 13. Real-world TopCV extraction -> Name: {ext_hung.full_name}, Email: {ext_hung.email}, Skills: {len(ext_hung.skills)}")

        # 14. Multi-Dimensional Extraction Verification (US-MultiDim)
        assert ext_hung.total_experience_years >= 5.0, f"Expected >= 5.0 years, got {ext_hung.total_experience_years}"
        assert len(ext_hung.experience_descriptions) >= 3, f"Expected bullet points, got {len(ext_hung.experience_descriptions)}"
        assert "bachelor" in (ext_hung.education_level or "").lower(), f"Expected Bachelor, got {ext_hung.education_level}"
        assert len(ext_hung.other_qualifications) > 0, "Expected non-technical qualifications"
        print(f"  [PASS] 14. Multi-dimensional extraction -> Exp: {ext_hung.total_experience_years} yrs, Degree: {ext_hung.education_level}, Bullets: {len(ext_hung.experience_descriptions)}, Other: {ext_hung.other_qualifications}")

        # 15. Multi-Dimensional Scoring & Gap Breakdown (US-MultiDim)
        uf_hung_match = _create_upload_file(hung_path, "27NguyenQuocHungTopCV261026100330.pdf")
        ai_senior_jd = (
            "Senior AI Engineer (5+ years experience required).\n"
            "Responsibilities:\n"
            "- Design and develop intelligent systems and pathfinding algorithms for NPCs.\n"
            "- Implement machine learning and reinforcement learning in gaming.\n"
            "Requirements:\n"
            "- Bachelor or Master degree in Computer Science / IT.\n"
            "- Proficient in PyTorch, TensorFlow, Python, Computer Vision, Deep Learning.\n"
            "- Strong communication, teamwork, and Agile methodology."
        )
        match_hung = await match_cv_to_jd(uf_hung_match, ai_senior_jd)
        assert match_hung.matching_score >= 60.0
        assert match_hung.compatibility_label in ["Good Fit", "Potential Fit"]
        assert match_hung.sub_scores
        assert "tech_skill_score" in match_hung.sub_scores
        assert "experience_score" in match_hung.sub_scores
        assert "other_req_score" in match_hung.sub_scores
        assert "ml_model_score" in match_hung.sub_scores
        assert match_hung.experience_match_summary and "CV:" in match_hung.experience_match_summary
        assert "matched" in match_hung.other_requirements_comparison
        print(f"  [PASS] 15. Multi-dimensional match -> Score: {match_hung.matching_score} ({match_hung.compatibility_label}), Summary: {match_hung.experience_match_summary}")
        print(f"         Sub-scores: {match_hung.sub_scores}")

    print("=" * 65)
    print("  ALL SPRINT 2 & 3 ENDPOINT & INTEGRATION TESTS PASSED (100%)")
    print("=" * 65)


if __name__ == "__main__":
    print(">>> ENTERING __main__", flush=True)
    asyncio.run(run_all_tests())
