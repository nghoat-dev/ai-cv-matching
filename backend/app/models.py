"""
SQLAlchemy ORM models for AI CV-Job Matching.

Tables:
  - cv_records       – uploaded CVs and extracted data
  - jd_records       – submitted job descriptions and processed data
  - matching_results – per-pair matching outputs
"""

from __future__ import annotations

import datetime
from typing import Any

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from backend.app.database import Base


def _utcnow() -> datetime.datetime:
    """Return the current UTC timestamp (timezone-naive for SQLite compat)."""
    return datetime.datetime.utcnow()


# ---------------------------------------------------------------------------
# CV Record
# ---------------------------------------------------------------------------


class CVRecord(Base):
    """Persisted representation of an uploaded CV."""

    __tablename__ = "cv_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    extracted_data: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=_utcnow, nullable=False
    )

    # Relationships
    matching_results: Mapped[list["MatchingResult"]] = relationship(
        "MatchingResult", back_populates="cv", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<CVRecord id={self.id} filename={self.filename!r}>"


# ---------------------------------------------------------------------------
# JD Record
# ---------------------------------------------------------------------------


class JDRecord(Base):
    """Persisted representation of a submitted Job Description."""

    __tablename__ = "jd_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    jd_text: Mapped[str] = mapped_column(Text, nullable=False)
    processed_data: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=_utcnow, nullable=False
    )

    # Relationships
    matching_results: Mapped[list["MatchingResult"]] = relationship(
        "MatchingResult", back_populates="jd", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<JDRecord id={self.id}>"


# ---------------------------------------------------------------------------
# Matching Result
# ---------------------------------------------------------------------------


class MatchingResult(Base):
    """Persisted result of a CV-to-JD matching operation."""

    __tablename__ = "matching_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    cv_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("cv_records.id", ondelete="CASCADE"), nullable=False
    )
    jd_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("jd_records.id", ondelete="CASCADE"), nullable=False
    )
    matching_score: Mapped[float] = mapped_column(Float, nullable=False)
    compatibility_label: Mapped[str] = mapped_column(String(20), nullable=False)
    matched_skills: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    missing_skills: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    llm_explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    llm_status: Mapped[str] = mapped_column(
        String(10), nullable=False, default="fallback"
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=_utcnow, nullable=False
    )

    # Relationships
    cv: Mapped["CVRecord"] = relationship("CVRecord", back_populates="matching_results")
    jd: Mapped["JDRecord"] = relationship("JDRecord", back_populates="matching_results")

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<MatchingResult id={self.id} score={self.matching_score} "
            f"label={self.compatibility_label!r}>"
        )
