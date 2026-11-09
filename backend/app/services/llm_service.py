"""
LLM Service for AI CV-Job Matching.

Handles communication with the configured LLM provider (default: Gemini) to
generate natural-language explanations of matching results.

Environment variables (loaded via python-dotenv / pydantic-settings):
  LLM_API_KEY       – API key for the LLM provider
  LLM_MODEL         – model identifier (default: gemini-1.5-flash)
  LLM_TIMEOUT       – request timeout in seconds (default: 15)
  LLM_TEMPERATURE   – sampling temperature (default: 0.2)
  LLM_MAX_TOKENS    – max output tokens (default: 1024)
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
from typing import Any

from dotenv import load_dotenv
import requests

load_dotenv()

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_MAX_TEXT_CHARS = 3_000  # max characters per text block sent to LLM
_FALLBACK_MESSAGE = "LLM service unavailable. ML-based analysis provided."
_GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"


# ---------------------------------------------------------------------------
# LLMService
# ---------------------------------------------------------------------------


class LLMService:
    """Thin wrapper around the configured LLM API.

    Parameters are read from environment variables so that no secrets are
    ever hard-coded in source files.
    """

    def __init__(self) -> None:
        # Explicitly reload .env in case it was created/modified after server startup
        from pathlib import Path
        possible_env_paths = [
            Path(__file__).resolve().parents[3] / ".env",
            Path(__file__).resolve().parents[2] / ".env",
            Path.cwd() / ".env",
        ]
        for env_path in possible_env_paths:
            if env_path.is_file():
                load_dotenv(env_path, override=True)
                break

        self.api_key: str = (
            os.getenv("LLM_API_KEY") or os.getenv("GEMINI_API_KEY") or ""
        ).strip().strip("'").strip('"')
        self.model: str = os.getenv("LLM_MODEL", "gemini-3.1-flash-lite").strip()
        self.timeout: int = int(os.getenv("LLM_TIMEOUT", "20"))
        self.temperature: float = float(os.getenv("LLM_TEMPERATURE", "0.2"))
        self.max_tokens: int = int(os.getenv("LLM_MAX_TOKENS", "1024"))

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate_explanation(
        self,
        cv_text: str,
        jd_text: str,
        matching_score: float,
        matched_skills: list[str] | None = None,
        missing_skills: list[str] | None = None,
        exp_summary: str | None = None,
    ) -> dict[str, Any]:
        """Generate a natural-language explanation for the matching result.

        Args:
            cv_text:        Raw text extracted from the candidate's CV.
            jd_text:        Original job description text.
            matching_score: Computed matching score (0–100).
            matched_skills: Matched technical skills list.
            missing_skills: Missing technical skills list.
            exp_summary:    Experience summary string.

        Returns:
            A dict with keys:
              - ``explanation`` (str): Human-readable analysis.
              - ``status`` (str): ``"success"`` or ``"fallback"``.
        """
        matched_str = ", ".join(matched_skills) if matched_skills else "None detected"
        missing_str = ", ".join(missing_skills) if missing_skills else "No critical skill gaps identified"
        verdict = "Good Fit" if matching_score >= 75.0 else ("Potential Fit" if matching_score >= 50.0 else "No Fit")
        fallback_analysis = (
            f"LLM service unavailable. ML-based analysis provided.\n"
            f"• Overall Verdict ({matching_score:.1f}/100 — {verdict}): {exp_summary or 'Evaluated via 4-dimensional scoring engine.'}\n"
            f"• Verified Technical Strengths: {matched_str}.\n"
            f"• Skill Gaps & Actionable Advice: "
            + (
                f"Candidate should strengthen or highlight experience in {missing_str} to improve alignment."
                if missing_skills
                else "All explicit technical skills in the JD are covered; verify practical project depth during interview."
            )
        )

        if not self.api_key:
            logger.warning("LLM_API_KEY not set – returning fallback explanation.")
            return {"explanation": fallback_analysis, "status": "fallback"}

        prompt = self._build_prompt(cv_text, jd_text, matching_score)

        # Attempt with one automatic retry on rate-limit (429)
        for attempt in range(2):
            try:
                explanation = self._call_api(prompt)
                return {"explanation": explanation, "status": "success"}

            except _AuthError as exc:
                logger.error("LLM authentication error: %s", exc)
                return {
                    "explanation": f"LLM Auth Error: Please verify your Gemini API key ({exc})",
                    "status": "fallback",
                }

            except requests.Timeout:
                logger.warning("LLM request timed out after %ss.", self.timeout)
                return {
                    "explanation": f"LLM request timed out after {self.timeout}s. Fallback heuristics applied.",
                    "status": "fallback",
                }

            except _RateLimitError:
                if attempt == 0:
                    logger.warning("LLM rate-limited (429) – retrying once after 2 s.")
                    time.sleep(2)
                    continue
                logger.error("LLM rate-limit persists after retry – returning fallback.")
                return {
                    "explanation": "Gemini API rate-limit exceeded (429). Please try again shortly.",
                    "status": "fallback",
                }

            except _MalformedOutputError as exc:
                logger.warning("LLM returned malformed output: %s", exc)
                return {"explanation": fallback_analysis, "status": "fallback"}

            except Exception as exc:  # pylint: disable=broad-except
                logger.error("Unexpected LLM error: %s", exc, exc_info=True)
                return {
                    "explanation": f"LLM error ({type(exc).__name__}): {exc}",
                    "status": "fallback",
                }

        # Should never be reached, but satisfy the type checker
        return {"explanation": fallback_analysis, "status": "fallback"}

    def extract_cv_with_llm(self, cv_text: str) -> dict[str, Any] | None:
        """Extract multi-dimensional CV data using LLM structured JSON output.

        Returns None if LLM is unavailable or output cannot be parsed.
        """
        if not self.api_key:
            return None

        prompt = (
            "You are an expert HR recruitment parser. Extract structured candidate information from the CV below.\n"
            "Ground all extracted information strictly in the provided text. Do not invent or hallucinate data.\n\n"
            f"### CV Text:\n{self._truncate(cv_text)}\n\n"
            "Return ONLY a valid JSON object with the exact keys:\n"
            "{\n"
            '  "technical_skills": ["python", "docker", ...],\n'
            '  "total_experience_years": 3.5,\n'
            '  "experience_descriptions": ["Designed microservices...", "Led backend team..."],\n'
            '  "education_level": "Bachelor" | "Master" | "PhD" | null,\n'
            '  "other_qualifications": ["IELTS 7.5", "Agile", "Teamwork", ...]\n'
            "}\n"
            "No markdown formatting, no commentary, strictly raw JSON."
        )

        try:
            raw_output = self._call_api(prompt)
            # Strip code block fences if returned
            clean_json = re.sub(r"^```(?:json)?\s*", "", raw_output.strip())
            clean_json = re.sub(r"\s*```$", "", clean_json)
            data = json.loads(clean_json)
            if isinstance(data, dict):
                return {
                    "technical_skills": list(data.get("technical_skills", [])),
                    "total_experience_years": float(data.get("total_experience_years", 0.0)),
                    "experience_descriptions": [str(d) for d in data.get("experience_descriptions", [])],
                    "education_level": data.get("education_level"),
                    "other_qualifications": list(data.get("other_qualifications", [])),
                }
        except Exception as exc:
            logger.debug("LLM CV extraction failed or timed out: %s", exc)
        return None

    def extract_jd_with_llm(self, jd_text: str) -> dict[str, Any] | None:
        """Extract multi-dimensional JD requirements using LLM structured JSON output.

        Returns None if LLM is unavailable or output cannot be parsed.
        """
        if not self.api_key:
            return None

        prompt = (
            "You are an expert HR recruitment parser. Extract structured job requirements from the Job Description below.\n"
            "Ground all extracted information strictly in the provided text. Do not invent or hallucinate data.\n\n"
            f"### Job Description:\n{self._truncate(jd_text)}\n\n"
            "Return ONLY a valid JSON object with the exact keys:\n"
            "{\n"
            '  "job_title": "Senior Backend Developer" | null,\n'
            '  "required_technical_skills": ["python", "fastapi", "docker", ...],\n'
            '  "min_experience_years": 2.0,\n'
            '  "job_responsibilities": ["Develop scalable APIs...", "Maintain CI/CD..."],\n'
            '  "required_education": "Bachelor" | "Master" | null,\n'
            '  "other_requirements": ["English fluency", "Agile/Scrum", "Communication", ...]\n'
            "}\n"
            "No markdown formatting, no commentary, strictly raw JSON."
        )

        try:
            raw_output = self._call_api(prompt)
            clean_json = re.sub(r"^```(?:json)?\s*", "", raw_output.strip())
            clean_json = re.sub(r"\s*```$", "", clean_json)
            data = json.loads(clean_json)
            if isinstance(data, dict):
                return {
                    "job_title": data.get("job_title"),
                    "required_technical_skills": list(data.get("required_technical_skills", [])),
                    "min_experience_years": float(data.get("min_experience_years", 0.0)),
                    "job_responsibilities": [str(d) for d in data.get("job_responsibilities", [])],
                    "required_education": data.get("required_education"),
                    "other_requirements": list(data.get("other_requirements", [])),
                }
        except Exception as exc:
            logger.debug("LLM JD extraction failed or timed out: %s", exc)
        return None

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _truncate(text: str) -> str:
        """Truncate *text* to at most ``_MAX_TEXT_CHARS`` characters."""
        if len(text) > _MAX_TEXT_CHARS:
            return text[:_MAX_TEXT_CHARS] + "\n...[truncated]"
        return text

    def _build_prompt(
        self, cv_text: str, jd_text: str, matching_score: float
    ) -> str:
        """Construct the prompt sent to the LLM."""
        cv_snippet = self._truncate(cv_text)
        jd_snippet = self._truncate(jd_text)
        return (
            f"You are an expert HR analyst. Analyse the CV and Job Description below "
            f"and explain why the candidate received a matching score of "
            f"{matching_score:.1f}/100.\n\n"
            f"### CV\n{cv_snippet}\n\n"
            f"### Job Description\n{jd_snippet}\n\n"
            f"Provide a concise, constructive explanation (3-5 sentences) covering "
            f"strengths, gaps, and a recommendation."
        )

    def _call_api(self, prompt: str) -> str:
        """Call the Gemini REST API and return the text response.

        Raises:
            _AuthError:           On HTTP 401 / 403.
            _RateLimitError:      On HTTP 429.
            _MalformedOutputError: When the response JSON has an unexpected shape.
            requests.Timeout:     When the request exceeds ``self.timeout``.
        """
        url = f"{_GEMINI_API_BASE}/{self.model}:generateContent?key={self.api_key}"
        payload: dict[str, Any] = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": self.temperature,
                "maxOutputTokens": self.max_tokens,
            },
        }

        response = requests.post(url, json=payload, timeout=self.timeout)

        # Auto-fallback to gemini-3.1-flash-lite if the requested model returns 404 (deprecated/unsupported)
        if response.status_code == 404 and self.model != "gemini-3.1-flash-lite":
            logger.warning("Gemini model '%s' returned 404 Not Found. Auto-falling back to gemini-3.1-flash-lite", self.model)
            self.model = "gemini-3.1-flash-lite"
            fallback_url = f"{_GEMINI_API_BASE}/{self.model}:generateContent?key={self.api_key}"
            response = requests.post(fallback_url, json=payload, timeout=self.timeout)

        if response.status_code in (401, 403):
            raise _AuthError(f"HTTP {response.status_code}: {response.text[:200]}")

        if response.status_code == 429:
            raise _RateLimitError("Rate limit exceeded (HTTP 429).")

        response.raise_for_status()

        try:
            data = response.json()
            text: str = data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError, ValueError) as exc:
            raise _MalformedOutputError(
                f"Unexpected API response structure: {exc}"
            ) from exc

        return text.strip()


# ---------------------------------------------------------------------------
# Internal exception types
# ---------------------------------------------------------------------------


class _AuthError(Exception):
    """Raised when the LLM API returns an authentication/authorisation error."""


class _RateLimitError(Exception):
    """Raised when the LLM API signals a rate-limit (HTTP 429)."""


class _MalformedOutputError(Exception):
    """Raised when the LLM response cannot be parsed as expected."""
