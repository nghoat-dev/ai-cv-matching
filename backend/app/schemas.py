"""
Pydantic schemas for AI CV-Job Matching API.

Defines all request/response models used across the API endpoints,
conforming to US-01 acceptance criteria.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


# ---------------------------------------------------------------------------
# US-01: CV Upload & Extraction
# ---------------------------------------------------------------------------


class CVUploadRequest(BaseModel):
    """Schema for the CV upload multipart/form-data request.

    Note: The actual ``pdf_file`` field is received as an UploadFile in the
    FastAPI endpoint; this schema documents the accompanying ``jd_text`` field
    and any metadata that travels alongside the file.
    """

    model_config = ConfigDict(extra="forbid")

    jd_text: str = Field(
        ...,
        min_length=1,
        description="Job description text (non-empty).",
    )


# ---------------------------------------------------------------------------
# Multi-Dimensional Extraction Schemas
# ---------------------------------------------------------------------------


class CVExtractedData(BaseModel):
    """Structured candidate data extracted across multiple dimensions."""

    model_config = ConfigDict(extra="ignore")

    full_name: str | None = Field(None, description="Candidate full name.")
    email: str | None = Field(None, description="Candidate e-mail address.")
    phone: str | None = Field(None, description="Candidate phone number.")
    technical_skills: list[str] = Field(
        default_factory=list,
        description="Programming languages, frameworks, libraries, databases, devops tools.",
    )
    total_experience_years: float = Field(
        default=0.0,
        description="Calculated work experience in years (explicit or date-range sum).",
    )
    experience_descriptions: list[str] = Field(
        default_factory=list,
        description="Bullet points of actual work/project responsibilities and achievements.",
    )
    education_level: str | None = Field(
        None,
        description="Highest detected degree/level (e.g. Bachelor, Master, PhD, Associate).",
    )
    other_qualifications: list[str] = Field(
        default_factory=list,
        description="Foreign languages (e.g. IELTS/TOEIC), certifications, soft skills, domain qualifications.",
    )
    raw_text: str = Field("", description="Raw text extracted from PDF.")


class JDExtractedData(BaseModel):
    """Structured requirements extracted from Job Description across multiple dimensions."""

    model_config = ConfigDict(extra="ignore")

    job_title: str | None = Field(None, description="Inferred or explicit job title.")
    required_technical_skills: list[str] = Field(
        default_factory=list,
        description="Hard technical skills required by the role.",
    )
    min_experience_years: float = Field(
        default=0.0,
        description="Minimum years of experience required (0.0 for fresher/intern).",
    )
    job_responsibilities: list[str] = Field(
        default_factory=list,
        description="Key duties and domain tasks required by the role.",
    )
    required_education: str | None = Field(
        None,
        description="Required education level (e.g. Bachelor, Master, etc.).",
    )
    other_requirements: list[str] = Field(
        default_factory=list,
        description="Soft skills, foreign languages, certifications, working methods (Agile/Scrum).",
    )
    normalized_jd_text: str = Field("", description="Normalized JD text.")


class CVExtractionResult(BaseModel):
    """Result produced by the CV extraction pipeline (Sprint 3 + Multi-Dimensional)."""

    model_config = ConfigDict(extra="forbid")

    full_name: str | None = Field(None, description="Candidate full name, if found.")
    email: str | None = Field(None, description="Candidate e-mail address, if found.")
    skills: list[str] = Field(default_factory=list, description="List of extracted skills (legacy alias).")
    technical_skills: list[str] = Field(default_factory=list, description="Extracted technical skills.")
    total_experience_years: float = Field(default=0.0, description="Total work experience in years.")
    experience_descriptions: list[str] = Field(
        default_factory=list,
        description="Bullet points of actual work/project responsibilities and achievements.",
    )
    education_level: str | None = Field(None, description="Education level / degree.")
    other_qualifications: list[str] = Field(
        default_factory=list,
        description="Foreign languages, certifications, soft skills, domain knowledge.",
    )
    education: list[dict[str, Any]] = Field(
        default_factory=list,
        description="List of education entries (degree, institution, year, …).",
    )
    work_experience: list[dict[str, Any]] = Field(
        default_factory=list,
        description="List of work-experience entries (title, company, duration, …).",
    )
    raw_text: str = Field(..., description="Full raw text extracted from the PDF.")


# ---------------------------------------------------------------------------
# US-01: JD Processing
# ---------------------------------------------------------------------------


class JDProcessingResult(BaseModel):
    """Result produced by the Job Description processing pipeline."""

    model_config = ConfigDict(extra="forbid")

    job_title: str = Field(..., description="Inferred or explicit job title.")
    required_skills: list[str] = Field(
        default_factory=list,
        description="List of skills required by the JD.",
    )
    experience_level: str | None = Field(
        None,
        description="Experience level (e.g. 'Junior', 'Mid', 'Senior'), if determinable.",
    )
    normalized_jd_text: str = Field(
        ..., description="Cleaned and normalized version of the original JD text."
    )


# ---------------------------------------------------------------------------
# US-01: Matching Response
# ---------------------------------------------------------------------------


class MatchingResponse(BaseModel):
    """Final matching result returned to the caller."""

    model_config = ConfigDict(extra="forbid")

    matching_score: float = Field(
        ...,
        description="Overall matching score between 0.0 and 100.0.",
    )
    compatibility_label: Literal["Good Fit", "Potential Fit", "No Fit"] = Field(
        ...,
        description="Human-readable compatibility bucket.",
    )
    matched_skills: list[str] = Field(
        default_factory=list,
        description="Skills present in both CV and JD.",
    )
    missing_skills: list[str] = Field(
        default_factory=list,
        description="Skills required by the JD but absent from the CV.",
    )
    experience_match_summary: str | None = Field(
        default=None,
        description="Detailed comparison of years and role responsibilities alignment.",
    )
    other_requirements_comparison: dict[str, Any] = Field(
        default_factory=lambda: {"matched": [], "missing": []},
        description="Matched vs missing non-technical requirements (education, soft skills, languages, certs).",
    )
    sub_scores: dict[str, float] = Field(
        default_factory=dict,
        description="Multi-dimensional sub-scores (tech_skill_score, experience_score, other_req_score, ml_model_score).",
    )
    cv_data: CVExtractedData | None = Field(
        default=None,
        description="Structured multi-dimensional CV data.",
    )
    jd_data: JDExtractedData | None = Field(
        default=None,
        description="Structured multi-dimensional JD data.",
    )
    llm_explanation: str | None = Field(
        None,
        description="Natural-language explanation generated by the LLM, if available.",
    )
    llm_status: Literal["success", "fallback"] = Field(
        ...,
        description="'success' when the LLM call succeeded; 'fallback' otherwise.",
    )

    @field_validator("matching_score")
    @classmethod
    def score_in_range(cls, v: float) -> float:
        """Ensure matching_score is within the valid [0.0, 100.0] range."""
        if not (0.0 <= v <= 100.0):
            raise ValueError(
                f"matching_score must be between 0.0 and 100.0, got {v!r}"
            )
        return v


# ---------------------------------------------------------------------------
# US-01: Error Response
# ---------------------------------------------------------------------------


class ErrorResponse(BaseModel):
    """Standardised error payload returned on 4xx / 5xx responses."""

    model_config = ConfigDict(extra="forbid")

    error_code: str = Field(..., description="Machine-readable error code.")
    message: str = Field(..., description="Human-readable error description.")
    details: dict[str, Any] = Field(
        default_factory=dict,
        description="Optional additional context about the error.",
    )
