"""
FastAPI application entry-point for AI CV-Job Matching.

Sprint 2 & 3 Production Release:
- US-14: PyMuPDF PDF extraction, magic bytes check, encryption validation
- US-15: JD input validation & text normalization
- US-16: Structured CV & JD Information Extraction (cv_extractor service)
- US-17 & US-18: ML model inference with advanced pipeline v2 fallback to v1
- US-19: LLM explanation generation with robust guardrails
- US-20: SQLite persistence (CVRecord, JDRecord, MatchingResult)
- US-21: End-to-end FastAPI endpoints
- US-25: History search, filter by label/score, sort, pagination, and deletion
- US-26: Multi-CV candidate comparison and ranking (/api/v1/compare)
- US-27: History CSV / JSON export (/api/v1/history/export)
- US-29: Embedded modern single-page Web UI (/ and /app)
"""

from __future__ import annotations

import csv
import io
import logging
import re
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

load_dotenv()

# Path setup: project root and ml_pipeline
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))
_ML_DIR = _PROJECT_ROOT / "ml_pipeline"
if str(_ML_DIR) not in sys.path:
    sys.path.insert(0, str(_ML_DIR))

import fitz  # PyMuPDF
from fastapi import FastAPI, File, Form, HTTPException, Query, Request, Response, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from pydantic import ValidationError
from sqlalchemy import func

from backend.app.database import SessionLocal, create_tables
from backend.app.models import CVRecord, JDRecord, MatchingResult
from backend.app.schemas import CVExtractedData, CVExtractionResult, ErrorResponse, JDExtractedData, MatchingResponse
from backend.app.services.cv_extractor import CVExtractor
from backend.app.services.llm_service import LLMService
from backend.app.services.scorer import MultiDimensionalScorer
from backend.app.web_ui import WEB_UI_HTML
from ml_pipeline.preprocessing import normalize_text
from ml_pipeline.train_baseline import compute_matching_score, load_model_artifact

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Global model artifact cache
_MODEL_ARTIFACT: dict[str, Any] | None = None
_MAX_PDF_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB


# ---------------------------------------------------------------------------
# Lifespan Handler
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler — initializes DB tables and loads ML model."""
    global _MODEL_ARTIFACT
    logger.info("Initializing database tables...")
    create_tables()
    logger.info("Database tables initialized.")

    for model_filename in ["advanced_pipeline_v2.joblib", "baseline_pipeline_v1.joblib"]:
        model_path = _PROJECT_ROOT / "models" / model_filename
        if model_path.exists():
            try:
                _MODEL_ARTIFACT = load_model_artifact(model_path)
                logger.info("Loaded ML model artifact: %s", model_filename)
                break
            except Exception as exc:
                logger.warning("Could not load %s: %s", model_filename, exc)

    if _MODEL_ARTIFACT is None:
        logger.warning("No ML model artifact found — using heuristic scoring engine.")

    yield
    logger.info("Shutting down AI CV-Job Matching application.")


# ---------------------------------------------------------------------------
# Application Instance
# ---------------------------------------------------------------------------

app = FastAPI(
    title="AI CV-Job Matching API",
    description=(
        "Production REST API for Intelligent CV-Job Matching using Machine Learning "
        "and LLMs. Sprint 3 final release."
    ),
    version="3.0.0",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Exception Handlers
# ---------------------------------------------------------------------------


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Format HTTPException into standardized ErrorResponse JSON."""
    if isinstance(exc.detail, dict):
        err_code = exc.detail.get("error_code")
        message = exc.detail.get("message")
        details = exc.detail.get("details", {})
        if not err_code:
            err_code = (
                "INVALID_INPUT"
                if exc.status_code == status.HTTP_400_BAD_REQUEST
                else f"HTTP_{exc.status_code}"
            )
        if not message:
            message = str(exc.detail)
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                error_code=err_code,
                message=message,
                details=details,
            ).model_dump(),
        )

    err_code = "INVALID_INPUT" if exc.status_code == status.HTTP_400_BAD_REQUEST else f"HTTP_{exc.status_code}"
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error_code=err_code,
            message=str(exc.detail),
            details={},
        ).model_dump(),
    )


def _validate_jd_text(jd_text: str) -> str:
    """
    Validate Job Description text per US-15 and US-22.

    Returns stripped jd_text if valid.
    Raises:
      HTTPException 400: If empty or whitespace only.
      HTTPException 422: If len(jd_text.strip()) < 30 or alphabetic word count < 5.
    """
    if not jd_text or not jd_text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job description text cannot be empty or whitespace only.",
        )

    stripped = jd_text.strip()
    words = re.findall(r"[a-zA-Z]+", stripped)
    if len(stripped) < 30 or len(words) < 5:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error_code": "INVALID_JD_CONTENT",
                "message": "Job description is too short or invalid.",
            },
        )

    return stripped


@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError) -> JSONResponse:
    """Format Pydantic validation errors (422) into ErrorResponse JSON."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponse(
            error_code="VALIDATION_ERROR",
            message="Request validation failed.",
            details={"errors": exc.errors()},
        ).model_dump(),
    )


@app.exception_handler(Exception)
async def internal_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all handler for unexpected internal server errors."""
    logger.exception("Internal server error: %s", exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error_code="INTERNAL_SERVER_ERROR",
            message="An unexpected server error occurred. Please try again.",
            details={},
        ).model_dump(),
    )


# ---------------------------------------------------------------------------
# Helper: Safe UploadFile Reader
# ---------------------------------------------------------------------------


def _read_upload_file(upload_file: UploadFile) -> bytes:
    """Read bytes directly from underlying SpooledTemporaryFile to avoid thread deadlocks."""
    if hasattr(upload_file, "file") and hasattr(upload_file.file, "read"):
        contents = upload_file.file.read()
        if isinstance(contents, bytes):
            return contents
    return b""


# ---------------------------------------------------------------------------
# Helper: PDF Validation & PyMuPDF Extraction (US-14)
# ---------------------------------------------------------------------------


def _validate_and_extract_pdf(contents: bytes, filename: str) -> str:
    """
    Validate PDF magic bytes, size, and encryption, then extract text via PyMuPDF.
    Conforms strictly to US14-AC01 through US14-AC05.
    """
    # US14-AC02: Validate extension
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are accepted (.pdf extension required).",
        )

    # US14-AC03: File size check
    if len(contents) > _MAX_PDF_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"PDF file exceeds the 5 MB limit ({len(contents)} bytes received).",
        )

    # US14-AC02: Magic bytes validation (%PDF- within first 1024 bytes per ISO 32000-1)
    header_chunk = contents[:1024].lstrip()
    if not header_chunk.startswith(b"%PDF-"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid PDF format: file magic bytes do not match standard PDF (%PDF-).",
        )

    # US14-AC01 & US14-AC05: PyMuPDF parsing and encryption check
    raw_text = ""
    try:
        doc = fitz.open(stream=contents, filetype="pdf")
        if doc.is_encrypted:
            doc.close()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Encrypted or password-protected PDF files are not supported.",
            )
        for page in doc:
            raw_text += page.get_text() + "\n"
        doc.close()
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Corrupted or unreadable PDF file: {exc}",
        )

    return raw_text.strip()


# ---------------------------------------------------------------------------
# Helper: Run ML Inference
# ---------------------------------------------------------------------------


def _run_ml_matching(norm_cv: str, norm_jd: str) -> tuple[float, str]:
    """Execute ML model prediction using the loaded artifact."""
    global _MODEL_ARTIFACT

    if _MODEL_ARTIFACT is None:
        for m_name in ["advanced_pipeline_v2.joblib", "baseline_pipeline_v1.joblib"]:
            p = _PROJECT_ROOT / "models" / m_name
            if p.exists():
                try:
                    _MODEL_ARTIFACT = load_model_artifact(p)
                    break
                except Exception:
                    pass

    if _MODEL_ARTIFACT is not None:
        try:
            clf = _MODEL_ARTIFACT["classifier"]
            extractor = _MODEL_ARTIFACT["feature_extractor"]
            X = extractor.transform([norm_cv], [norm_jd])
            pred_class = int(clf.predict(X)[0])
            probs = clf.predict_proba(X)

            from ml_pipeline.scoring import compute_matching_score_v2
            score_val = float(compute_matching_score_v2(probs)[0])
            score = round(max(0.0, min(100.0, score_val)), 1)
            labels = ["No Fit", "Potential Fit", "Good Fit"]
            return score, labels[pred_class]
        except Exception as exc:
            logger.error("ML inference error: %s", exc)

    return 70.0, "Potential Fit"


# ---------------------------------------------------------------------------
# UI Routes: Serve Embedded Web Interface (US-29)
# ---------------------------------------------------------------------------


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
@app.get("/app", response_class=HTMLResponse, include_in_schema=False)
async def serve_web_ui() -> HTMLResponse:
    """Serve the complete, zero-dependency modern interactive single-page application."""
    return HTMLResponse(content=WEB_UI_HTML)


@app.get("/Documents/{filename}", include_in_schema=False)
async def serve_sample_document(filename: str):
    """Serve sample CV PDF files for one-click demo testing."""
    file_path = _PROJECT_ROOT / "Documents" / filename
    if not file_path.exists() or not filename.endswith(".pdf"):
        raise HTTPException(status_code=404, detail="Sample document not found.")
    return FileResponse(path=file_path, media_type="application/pdf", filename=filename)


# ---------------------------------------------------------------------------
# Health & Info Endpoints
# ---------------------------------------------------------------------------


@app.get("/health", summary="Health check", tags=["System"], response_model=dict)
async def health_check() -> dict[str, str]:
    """Return application liveness status."""
    return {"status": "healthy", "version": "3.0.0"}


@app.get("/api/v1/info", summary="API metadata", tags=["System"], response_model=dict)
async def api_info() -> dict[str, Any]:
    """Return descriptive metadata about the system, loaded model, and endpoints."""
    model_loaded = _MODEL_ARTIFACT is not None
    model_type = (
        _MODEL_ARTIFACT.get("metadata", {}).get("model_type", "Standard Classifier")
        if _MODEL_ARTIFACT
        else "None"
    )
    llm = LLMService()
    return {
        "name": "AI CV-Job Matching API",
        "version": "3.0.0",
        "sprint": "Sprint 3 Final Release",
        "model_loaded": model_loaded,
        "model_type": model_type,
        "llm_configured": bool(llm.api_key),
        "llm_model": llm.model if llm.api_key else None,
        "endpoints": {
            "POST   /api/v1/match": "Match CV PDF against Job Description.",
            "POST   /api/v1/extract": "Extract structured entities from CV PDF.",
            "POST   /api/v1/compare": "Multi-CV side-by-side comparison & ranking.",
            "GET    /api/v1/history": "Query, search, filter, and paginate matching history.",
            "DELETE /api/v1/history/{id}": "Delete matching record from history.",
            "GET    /api/v1/history/export": "Export matching history to CSV or JSON.",
            "GET    /api/v1/stats": "System-wide aggregate statistics.",
            "GET    /health": "Health check probe.",
            "GET    /app": "Interactive Web UI.",
        },
    }


# ---------------------------------------------------------------------------
# POST /api/v1/match — Core CV Matching Endpoint
# ---------------------------------------------------------------------------


@app.post(
    "/api/v1/match",
    summary="Match CV to Job Description",
    tags=["Matching"],
    response_model=MatchingResponse,
    status_code=status.HTTP_200_OK,
)
async def match_cv_to_jd(
    pdf_file: UploadFile = File(..., description="Candidate CV in PDF format (max 5 MB)."),
    jd_text: str = Form(..., min_length=1, description="Job description text."),
) -> MatchingResponse:
    """
    Upload CV PDF and Job Description text:
    1. Validate PDF format (%PDF-), size (<= 5MB), and encryption.
    2. Extract clean text with PyMuPDF.
    3. Normalize text and extract skills.
    4. Predict compatibility score and label with ML model.
    5. Generate LLM explanation and persist to database.
    """
    filename = pdf_file.filename or "uploaded_cv.pdf"

    # US-15 & US-22: Validate JD input
    valid_jd_text = _validate_jd_text(jd_text)

    contents = _read_upload_file(pdf_file)

    # US-14: Validate & extract PDF
    raw_cv_text = _validate_and_extract_pdf(contents, filename)
    effective_cv_text = raw_cv_text if raw_cv_text else f"Candidate Resume: {filename}"

    # Preprocessing
    norm_cv = normalize_text(effective_cv_text)
    norm_jd = normalize_text(valid_jd_text)

    # Multi-Dimensional Structured Extraction
    extractor_service = CVExtractor()
    cv_data = extractor_service.extract_cv_structured(effective_cv_text, pdf_bytes=contents)
    jd_data = extractor_service.extract_jd_structured(valid_jd_text)

    # ML Semantic Inference
    raw_ml_score, _ = _run_ml_matching(norm_cv, norm_jd)

    # Multi-Dimensional Scoring & Gap Analysis (Tech 45%, Exp 30%, Other 15%, ML 10%)
    scorer = MultiDimensionalScorer()
    score_result = scorer.compute_scores(cv_data, jd_data, raw_ml_score)

    matching_score = score_result["matching_score"]
    compatibility_label = score_result["compatibility_label"]
    matched = score_result["matched_skills"]
    missing = score_result["missing_skills"]
    sub_scores = score_result["sub_scores"]
    exp_summary = score_result["experience_match_summary"]
    other_comp = score_result["other_requirements_comparison"]

    # LLM Explanation (with fallback)
    llm_service = LLMService()
    llm_res = llm_service.generate_explanation(effective_cv_text, jd_text, matching_score)

    # Persist to database (US-20)
    try:
        db = SessionLocal()
        cv_rec = CVRecord(
            filename=filename,
            raw_text=effective_cv_text,
            extracted_data=cv_data.model_dump(),
        )
        db.add(cv_rec)
        db.flush()

        jd_rec = JDRecord(
            jd_text=jd_text,
            processed_data=jd_data.model_dump(),
        )
        db.add(jd_rec)
        db.flush()

        res_rec = MatchingResult(
            cv_id=cv_rec.id,
            jd_id=jd_rec.id,
            matching_score=matching_score,
            compatibility_label=compatibility_label,
            matched_skills=matched,
            missing_skills=missing,
            llm_explanation=llm_res["explanation"],
            llm_status=llm_res["status"],
        )
        db.add(res_rec)
        db.commit()
        db.close()
    except Exception as exc:
        logger.warning("Database persistence error: %s", exc)

    return MatchingResponse(
        matching_score=matching_score,
        compatibility_label=compatibility_label,
        matched_skills=matched,
        missing_skills=missing,
        experience_match_summary=exp_summary,
        other_requirements_comparison=other_comp,
        sub_scores=sub_scores,
        cv_data=cv_data,
        jd_data=jd_data,
        llm_explanation=llm_res["explanation"],
        llm_status=llm_res["status"],
    )


# ---------------------------------------------------------------------------
# POST /api/v1/extract — Standalone CV Entity Extraction (US-16)
# ---------------------------------------------------------------------------


@app.post(
    "/api/v1/extract",
    summary="Extract structured data from CV PDF",
    tags=["Extraction"],
    response_model=CVExtractionResult,
    status_code=status.HTTP_200_OK,
)
async def extract_cv_data(
    pdf_file: UploadFile = File(..., description="Candidate CV in PDF format (max 5 MB)."),
) -> CVExtractionResult:
    """Extract raw text and structured candidate fields (name, email, skills, education, experience)."""
    filename = pdf_file.filename or "cv.pdf"
    contents = _read_upload_file(pdf_file)
    raw_text = _validate_and_extract_pdf(contents, filename)

    extractor = CVExtractor()
    data = extractor.extract_structured_data(raw_text, pdf_bytes=contents)

    return CVExtractionResult(
        full_name=data["full_name"],
        email=data["email"],
        skills=data["skills"],
        technical_skills=data.get("technical_skills", data["skills"]),
        total_experience_years=data.get("total_experience_years", 0.0),
        experience_descriptions=data.get("experience_descriptions", []),
        education_level=data.get("education_level"),
        other_qualifications=data.get("other_qualifications", []),
        education=data["education"],
        work_experience=data["work_experience"],
        raw_text=raw_text,
    )


# ---------------------------------------------------------------------------
# POST /api/v1/compare — Multi-CV Comparison & Candidate Ranking (US-26)
# ---------------------------------------------------------------------------


@app.post(
    "/api/v1/compare",
    summary="Compare & Rank Multiple CVs for a Job Description",
    tags=["Matching"],
    response_model=dict,
    status_code=status.HTTP_200_OK,
)
async def compare_multiple_cvs(
    files: list[UploadFile] = File(..., description="List of candidate CV PDF files to compare."),
    jd_text: str = Form(..., min_length=1, description="Job description text."),
) -> dict[str, Any]:
    """
    Accept multiple CV PDF files and a single JD.
    Matches each candidate against the JD and returns a ranked leaderboard sorted by score.
    """
    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one CV PDF file must be provided.",
        )
    # US-15 & US-22: Validate JD input
    valid_jd_text = _validate_jd_text(jd_text)

    norm_jd = normalize_text(valid_jd_text)
    extractor = CVExtractor()
    jd_data = extractor.extract_jd_structured(valid_jd_text)
    scorer = MultiDimensionalScorer()

    candidates = []
    for file in files:
        fname = file.filename or "candidate.pdf"
        try:
            contents = _read_upload_file(file)
            raw_text = _validate_and_extract_pdf(contents, fname)
            norm_cv = normalize_text(raw_text)

            cv_data = extractor.extract_cv_structured(raw_text, pdf_bytes=contents)
            raw_score, _ = _run_ml_matching(norm_cv, norm_jd)

            score_res = scorer.compute_scores(cv_data, jd_data, raw_score)

            candidates.append({
                "filename": fname,
                "score": score_res["matching_score"],
                "compatibility_label": score_res["compatibility_label"],
                "matched_skills": score_res["matched_skills"],
                "missing_skills": score_res["missing_skills"],
                "experience_match_summary": score_res["experience_match_summary"],
                "sub_scores": score_res["sub_scores"],
            })
        except Exception as exc:
            logger.warning("Error processing CV '%s' in comparison: %s", fname, exc)
            candidates.append({
                "filename": fname,
                "score": 0.0,
                "compatibility_label": "No Fit",
                "matched_skills": [],
                "missing_skills": [],
                "error": str(exc),
            })

    # Rank by descending score
    candidates.sort(key=lambda c: c["score"], reverse=True)
    for rank_idx, c in enumerate(candidates, 1):
        c["rank"] = rank_idx

    return {
        "total_candidates": len(candidates),
        "candidates": candidates,
    }


# ---------------------------------------------------------------------------
# GET /api/v1/history — Filterable & Searchable History (US-25)
# ---------------------------------------------------------------------------


@app.get(
    "/api/v1/history",
    summary="Get matching history",
    tags=["History"],
    response_model=dict,
    status_code=status.HTTP_200_OK,
)
async def get_history(
    limit: int = Query(default=20, ge=1, le=100, description="Max records to return."),
    offset: int = Query(default=0, ge=0, description="Pagination offset."),
    search: str | None = Query(default=None, description="Keyword search in filename or label."),
    label: str | None = Query(default=None, description="Filter by compatibility label."),
    min_score: float | None = Query(default=None, ge=0.0, le=100.0, description="Min matching score."),
    max_score: float | None = Query(default=None, ge=0.0, le=100.0, description="Max matching score."),
    sort_by: str = Query(default="newest", description="'newest', 'oldest', 'highest_score', 'lowest_score'"),
) -> dict[str, Any]:
    """Retrieve past matching records with search, label filtering, score filtering, and sorting."""
    # Handle default query objects when invoked directly in tests
    search_val = search if isinstance(search, str) and search.strip() else None
    label_val = label if isinstance(label, str) and label.strip() else None
    min_score_val = min_score if isinstance(min_score, (int, float)) else None
    max_score_val = max_score if isinstance(max_score, (int, float)) else None
    sort_by_val = sort_by if isinstance(sort_by, str) else "newest"
    limit_val = limit if isinstance(limit, int) else 20
    offset_val = offset if isinstance(offset, int) else 0

    try:
        db = SessionLocal()
        query = db.query(MatchingResult).join(CVRecord, MatchingResult.cv_id == CVRecord.id, isouter=True)

        # Filters
        if label_val:
            query = query.filter(MatchingResult.compatibility_label == label_val)
        if min_score_val is not None:
            query = query.filter(MatchingResult.matching_score >= min_score_val)
        if max_score_val is not None:
            query = query.filter(MatchingResult.matching_score <= max_score_val)
        if search_val:
            search_pat = f"%{search_val.strip()}%"
            query = query.filter(
                (CVRecord.filename.ilike(search_pat))
                | (MatchingResult.compatibility_label.ilike(search_pat))
            )

        total = query.count()

        # Sorting
        if sort_by_val == "oldest":
            query = query.order_by(MatchingResult.created_at.asc())
        elif sort_by_val == "highest_score":
            query = query.order_by(MatchingResult.matching_score.desc())
        elif sort_by_val == "lowest_score":
            query = query.order_by(MatchingResult.matching_score.asc())
        else:
            query = query.order_by(MatchingResult.created_at.desc())

        rows = query.offset(offset_val).limit(limit_val).all()

        results = []
        for r in rows:
            cv_filename = "Unknown"
            if r.cv:
                cv_filename = r.cv.filename
            results.append({
                "id": r.id,
                "cv_filename": cv_filename,
                "matching_score": r.matching_score,
                "compatibility_label": r.compatibility_label,
                "matched_skills": r.matched_skills or [],
                "missing_skills": r.missing_skills or [],
                "llm_explanation": r.llm_explanation,
                "llm_status": r.llm_status,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            })

        db.close()
        return {
            "total": total,
            "count": len(results),
            "limit": limit,
            "offset": offset,
            "results": results,
        }
    except Exception as exc:
        logger.error("Failed to fetch history: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not retrieve history from database.",
        )


# ---------------------------------------------------------------------------
# DELETE /api/v1/history/{result_id} — Delete Record (US-25)
# ---------------------------------------------------------------------------


@app.delete(
    "/api/v1/history/{result_id}",
    summary="Delete matching record",
    tags=["History"],
    response_model=dict,
    status_code=status.HTTP_200_OK,
)
async def delete_history_record(result_id: int) -> dict[str, Any]:
    """Delete a matching result record by its ID."""
    try:
        db = SessionLocal()
        record = db.query(MatchingResult).filter(MatchingResult.id == result_id).first()
        if not record:
            db.close()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Matching record with ID {result_id} not found.",
            )
        db.delete(record)
        db.commit()
        db.close()
        return {"message": "Record deleted successfully", "id": result_id}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Failed to delete record %d: %s", result_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete record.",
        )


# ---------------------------------------------------------------------------
# GET /api/v1/history/export — CSV & JSON Export (US-27)
# ---------------------------------------------------------------------------


@app.get(
    "/api/v1/history/export",
    summary="Export matching history",
    tags=["History"],
    status_code=status.HTTP_200_OK,
)
async def export_history(
    format: str = Query(default="csv", pattern="^(csv|json)$", description="Export format: 'csv' or 'json'"),
) -> Response:
    """Export all matching history records as a downloadable CSV or JSON file."""
    format_val = format if isinstance(format, str) else "csv"
    try:
        db = SessionLocal()
        records = db.query(MatchingResult).order_by(MatchingResult.created_at.desc()).all()

        if format_val == "json":
            data = []
            for r in records:
                fname = r.cv.filename if r.cv else "Unknown"
                data.append({
                    "id": r.id,
                    "cv_filename": fname,
                    "matching_score": r.matching_score,
                    "compatibility_label": r.compatibility_label,
                    "matched_skills": r.matched_skills or [],
                    "missing_skills": r.missing_skills or [],
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                })
            db.close()
            return JSONResponse(
                content=data,
                headers={"Content-Disposition": "attachment; filename=matching_history.json"},
            )

        # CSV format
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["ID", "CV Filename", "Matching Score", "Compatibility", "Matched Skills", "Missing Skills", "Created At"])

        for r in records:
            fname = r.cv.filename if r.cv else "Unknown"
            matched_str = "; ".join(r.matched_skills or [])
            missing_str = "; ".join(r.missing_skills or [])
            created = r.created_at.isoformat() if r.created_at else ""
            writer.writerow([r.id, fname, f"{r.matching_score:.1f}", r.compatibility_label, matched_str, missing_str, created])

        db.close()
        csv_content = output.getvalue()
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=matching_history_export.csv"},
        )
    except Exception as exc:
        logger.error("Failed to export history: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export history records.",
        )


# ---------------------------------------------------------------------------
# GET /api/v1/stats — Aggregate Analytics (US-28)
# ---------------------------------------------------------------------------


@app.get(
    "/api/v1/stats",
    summary="Get aggregate system statistics",
    tags=["Analytics"],
    response_model=dict,
    status_code=status.HTTP_200_OK,
)
async def get_stats() -> dict[str, Any]:
    """Return aggregate statistics across all matching records."""
    try:
        db = SessionLocal()
        total_matches = db.query(MatchingResult).count()
        total_cvs = db.query(CVRecord).count()
        total_jds = db.query(JDRecord).count()

        avg_score = None
        score_range = {"min": None, "max": None}
        label_dist: dict[str, int] = {"Good Fit": 0, "Potential Fit": 0, "No Fit": 0}

        if total_matches > 0:
            agg = db.query(
                func.avg(MatchingResult.matching_score),
                func.min(MatchingResult.matching_score),
                func.max(MatchingResult.matching_score),
            ).first()
            if agg:
                avg_score = round(float(agg[0]), 2) if agg[0] is not None else None
                score_range = {
                    "min": round(float(agg[1]), 1) if agg[1] is not None else None,
                    "max": round(float(agg[2]), 1) if agg[2] is not None else None,
                }

            for lbl in label_dist:
                label_dist[lbl] = db.query(MatchingResult).filter(MatchingResult.compatibility_label == lbl).count()

        db.close()
        return {
            "total_matches": total_matches,
            "total_cvs": total_cvs,
            "total_jds": total_jds,
            "avg_score": avg_score,
            "score_range": score_range,
            "label_distribution": label_dist,
        }
    except Exception as exc:
        logger.error("Failed to fetch statistics: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not compute system statistics.",
        )
