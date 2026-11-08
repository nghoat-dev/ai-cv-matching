"""
Multi-Dimensional Scoring and Gap Analyzer for AI CV-Job Matching.

Implements the multi-dimensional scoring engine combining:
1. Technical Skill Coverage (45% weight)
2. Experience & Role Alignment (30% weight: quantitative comparison + TF-IDF cosine similarity)
3. Education & Other Requirements Coverage (15% weight: degree, soft skills, languages, certifications)
4. ML Semantic Pipeline Model (10% weight)
"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from backend.app.schemas import CVExtractedData, JDExtractedData
from backend.app.services.cv_extractor import (
    DEGREE_HIERARCHY,
    OTHER_REQUIREMENTS_TAXONOMY,
    TECH_SKILLS_TAXONOMY,
    extract_experience_and_responsibility_lines,
    extract_experience_years,
    extract_taxonomy_items,
)

logger = logging.getLogger(__name__)


def evaluate_comprehensive_match(
    cv_text: str, jd_text: str, ml_prob_score: float = 70.0
) -> dict[str, Any]:
    """
    Hàm chấm điểm toàn diện 4 chiều trực tiếp từ văn bản thô:
    1. Kỹ năng kỹ thuật (45%)
    2. Kinh nghiệm làm việc & Độ khớp trách nhiệm dự án (30%)
    3. Yêu cầu khác của JD: Học vấn, Ngoại ngữ, Quy trình, Kỹ năng mềm (15%)
    4. Điểm xác suất từ mô hình ML (10%)
    """
    # --- 1. KỸ THUẬT & CÔNG CỤ (45%) ---
    cv_tech = set(extract_taxonomy_items(cv_text, TECH_SKILLS_TAXONOMY))
    jd_tech = set(extract_taxonomy_items(jd_text, TECH_SKILLS_TAXONOMY))
    matched_tech = sorted(list(cv_tech & jd_tech))
    missing_tech = sorted(list(jd_tech - cv_tech))
    if jd_tech:
        tech_coverage = (len(matched_tech) / len(jd_tech) * 100.0)
    elif cv_tech:
        tech_coverage = 40.0
    else:
        tech_coverage = 0.0

    # --- 2. KINH NGHIỆM & TRÁCH NHIỆM CÔNG VIỆC (30%) ---
    cv_years = extract_experience_years(cv_text, is_jd=False)
    jd_years = extract_experience_years(jd_text, is_jd=True)

    if jd_years > 0.0:
        if cv_years >= jd_years:
            years_score = 100.0
        else:
            years_score = max(10.0, (cv_years / jd_years) * 100.0)
    else:
        years_score = 60.0 if cv_years > 0.0 else 10.0

    cv_exp_lines = " ".join(extract_experience_and_responsibility_lines(cv_text))
    jd_resp_lines = " ".join(extract_experience_and_responsibility_lines(jd_text))
    if cv_exp_lines and jd_resp_lines:
        try:
            vec = TfidfVectorizer(ngram_range=(1, 2), stop_words="english", max_features=3000)
            tfidf_mat = vec.fit_transform([cv_exp_lines, jd_resp_lines])
            raw_sim = float(cosine_similarity(tfidf_mat[0:1], tfidf_mat[1:2])[0][0])
            resp_similarity_score = min(100.0, round((raw_sim / 0.35) * 100.0, 1))
        except Exception as exc:
            logger.debug("TF-IDF cosine similarity fallback: %s", exc)
            resp_similarity_score = 20.0
    else:
        resp_similarity_score = 0.0

    experience_total_score = round(0.50 * years_score + 0.50 * resp_similarity_score, 1)

    # --- 3. YÊU CẦU KHÁC (HỌC VẤN, NGOẠI NGỮ, QUY TRÌNH, SOFT SKILLS) (15%) ---
    cv_other = set(extract_taxonomy_items(cv_text, OTHER_REQUIREMENTS_TAXONOMY))
    jd_other = set(extract_taxonomy_items(jd_text, OTHER_REQUIREMENTS_TAXONOMY))

    # Xử lý bằng cấp phân tầng
    cv_degree_rank = max([DEGREE_HIERARCHY.get(k, 0) for k in cv_other], default=0)
    jd_degree_rank = max([DEGREE_HIERARCHY.get(k, 0) for k in jd_other], default=0)
    degree_satisfied = cv_degree_rank >= jd_degree_rank

    matched_other = sorted(list(cv_other & jd_other))
    missing_other = sorted(list(jd_other - cv_other))

    # Nếu ứng viên có bậc học cao hơn bằng yêu cầu (VD: Thạc sĩ đạt chuẩn Cử nhân)
    if jd_degree_rank > 0 and degree_satisfied:
        for deg_name in ["Bachelor's Degree", "Master's Degree"]:
            if deg_name in missing_other and cv_degree_rank >= DEGREE_HIERARCHY.get(deg_name, 0):
                missing_other.remove(deg_name)
                matched_other.append(f"{deg_name} (Satisfied by higher degree)")

    if jd_other:
        other_req_score = (len(matched_other) / len(jd_other) * 100.0)
    elif cv_other:
        other_req_score = 40.0
    else:
        other_req_score = 0.0

    # --- 4. TỔNG HỢP ĐIỂM (0 - 100) VỚI ĐÚNG TRỌNG SỐ TOÁN HỌC ---
    tech_score = round(float(tech_coverage), 1)
    exp_score = round(float(experience_total_score), 1)
    edu_score = round(float(other_req_score), 1)
    ml_score = round(float(ml_prob_score), 1)

    final_score = round(
        0.45 * tech_score
        + 0.30 * exp_score
        + 0.15 * edu_score
        + 0.10 * ml_score,
        1,
    )
    final_score = round(float(np.clip(final_score, 0.0, 100.0)), 1)
    label = "Good Fit" if final_score >= 75.0 else ("Potential Fit" if final_score >= 50.0 else "No Fit")

    summary_str = (
        f"CV: {cv_years:.1f} yrs vs JD: {jd_years:.1f}+ yrs | Role alignment: {int(resp_similarity_score)}%"
        if jd_years > 0.0
        else f"CV: {cv_years:.1f} yrs vs JD: Entry Level | Role alignment: {int(resp_similarity_score)}%"
    )

    sub_scores = {
        "tech_skill_score": tech_score,
        "experience_score": exp_score,
        "other_req_score": edu_score,
        "ml_model_score": ml_score,
    }

    return {
        "matching_score": final_score,
        "compatibility_label": label,
        "matched_skills": matched_tech,
        "missing_skills": missing_tech,
        "matched_other_requirements": matched_other,
        "missing_other_requirements": missing_other,
        "sub_scores": sub_scores,
        "experience_match_summary": summary_str,
        "other_requirements_comparison": {
            "matched": matched_other,
            "missing": missing_other,
            "education": {
                "candidate_degree_rank": cv_degree_rank,
                "required_degree_rank": jd_degree_rank,
                "satisfied": degree_satisfied,
            },
        },
        "experience_analysis": {
            "cv_estimated_years": cv_years,
            "jd_required_years": jd_years,
            "years_match_score": round(years_score, 1),
            "responsibility_alignment_score": resp_similarity_score,
            "summary": summary_str,
        },
        "score_breakdown": {
            "technical_skills_score": round(tech_coverage, 1),
            "experience_and_responsibilities_score": experience_total_score,
            "other_jd_requirements_score": round(other_req_score, 1),
            "ml_model_confidence": round(ml_prob_score, 1),
        },
    }


class MultiDimensionalScorer:
    """Computes comprehensive 4-dimensional matching score and gap breakdown."""

    def __init__(self) -> None:
        pass

    def compute_scores(
        self,
        cv_data: CVExtractedData,
        jd_data: JDExtractedData,
        ml_model_score: float,
    ) -> dict[str, Any]:
        """Compute matching score from structured CVExtractedData and JDExtractedData objects."""
        # 1. Technical Skill Coverage
        cv_tech_lower = {s.lower() for s in cv_data.technical_skills}
        jd_tech_lower = {s.lower() for s in jd_data.required_technical_skills}

        if jd_tech_lower:
            matched_tech = [s for s in jd_data.required_technical_skills if s.lower() in cv_tech_lower]
            missing_tech = [s for s in jd_data.required_technical_skills if s.lower() not in cv_tech_lower]
            tech_skill_score = min(100.0, (len(matched_tech) / len(jd_tech_lower)) * 100.0)
        elif cv_tech_lower:
            matched_tech = cv_data.technical_skills[:5]
            missing_tech = []
            tech_skill_score = 40.0
        else:
            matched_tech = []
            missing_tech = []
            tech_skill_score = 0.0

        # 2. Experience & Role Alignment
        total_exp = cv_data.total_experience_years
        min_exp = jd_data.min_experience_years

        if min_exp > 0.0:
            if total_exp >= min_exp:
                quant_exp_score = 100.0
            else:
                ratio = total_exp / min_exp
                quant_exp_score = min(100.0, max(10.0, ratio * 100.0))
        else:
            quant_exp_score = 60.0 if total_exp > 0.0 else 10.0

        # Qualitative alignment via TF-IDF
        cv_exp_text = " ".join(cv_data.experience_descriptions) if cv_data.experience_descriptions else cv_data.raw_text
        jd_resp_text = " ".join(jd_data.job_responsibilities) if jd_data.job_responsibilities else jd_data.normalized_jd_text

        role_alignment_pct = 0.0
        if cv_exp_text.strip() and jd_resp_text.strip():
            try:
                vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words="english", max_features=3000)
                tfidf_matrix = vectorizer.fit_transform([cv_exp_text, jd_resp_text])
                sim = float(cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0])
                role_alignment_pct = min(100.0, max(0.0, (sim / 0.35) * 100.0))
            except Exception as exc:
                logger.debug("TF-IDF experience cosine similarity calculation fallback: %s", exc)
                role_alignment_pct = 20.0

        experience_score = round(0.50 * quant_exp_score + 0.50 * role_alignment_pct, 1)

        summary_str = (
            f"CV: {total_exp:.1f} yrs vs JD: {min_exp:.1f}+ yrs | Role alignment: {int(role_alignment_pct)}%"
            if min_exp > 0.0
            else f"CV: {total_exp:.1f} yrs vs JD: Entry Level | Role alignment: {int(role_alignment_pct)}%"
        )

        # 3. Education & Other Requirements Coverage
        cv_other = set(cv_data.other_qualifications)
        jd_other = set(jd_data.other_requirements)

        cv_degree_rank = max([DEGREE_HIERARCHY.get(k, 0) for k in cv_other], default=0)
        jd_degree_rank = max([DEGREE_HIERARCHY.get(k, 0) for k in jd_other], default=0)
        degree_satisfied = cv_degree_rank >= jd_degree_rank

        matched_other = sorted(list(cv_other & jd_other))
        missing_other = sorted(list(jd_other - cv_other))

        if jd_degree_rank > 0 and degree_satisfied:
            for deg_name in ["Bachelor's Degree", "Master's Degree"]:
                if deg_name in missing_other and cv_degree_rank >= DEGREE_HIERARCHY.get(deg_name, 0):
                    missing_other.remove(deg_name)
                    matched_other.append(f"{deg_name} (Satisfied by higher degree)")

        if jd_other:
            other_req_score = (len(matched_other) / len(jd_other) * 100.0)
        elif cv_other:
            other_req_score = 40.0
        else:
            other_req_score = 0.0

        # 4. ML Model Score & Exact Mathematical Weighted Sum (US-MultiDim)
        ml_score = round(float(np.clip(ml_model_score, 0.0, 100.0)), 1)
        tech_score = round(float(tech_skill_score), 1)
        exp_score = round(float(experience_score), 1)
        edu_score = round(float(other_req_score), 1)

        # Composite Multi-Dimensional Score: EXACT weighted sum
        final_score = round(
            0.45 * tech_score
            + 0.30 * exp_score
            + 0.15 * edu_score
            + 0.10 * ml_score,
            1,
        )
        final_score = round(float(np.clip(final_score, 0.0, 100.0)), 1)
        compatibility_label = (
            "Good Fit" if final_score >= 75.0 else ("Potential Fit" if final_score >= 50.0 else "No Fit")
        )

        sub_scores = {
            "tech_skill_score": tech_score,
            "experience_score": exp_score,
            "other_req_score": edu_score,
            "ml_model_score": ml_score,
        }

        return {
            "matching_score": final_score,
            "compatibility_label": compatibility_label,
            "matched_skills": matched_tech,
            "missing_skills": missing_tech,
            "matched_other_requirements": matched_other,
            "missing_other_requirements": missing_other,
            "sub_scores": sub_scores,
            "experience_match_summary": summary_str,
            "other_requirements_comparison": {
                "matched": matched_other,
                "missing": missing_other,
                "education": {
                    "candidate_degree_rank": cv_degree_rank,
                    "required_degree_rank": jd_degree_rank,
                    "satisfied": degree_satisfied,
                },
            },
        }
