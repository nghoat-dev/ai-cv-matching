"""
Seed rich demo data for Sprint 2 and 3 demonstration.

Populates cv_records, jd_records, and matching_results tables with diverse,
realistic candidates across software engineering, data science, accounting,
and marketing domains.
"""

from __future__ import annotations

import datetime
import random
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from backend.app.database import SessionLocal, create_tables
from backend.app.models import CVRecord, JDRecord, MatchingResult

DEMO_CANDIDATES = [
    {
        "filename": "Nguyen_Van_A_Senior_Python_Backend.pdf",
        "skills": ["Python", "FastAPI", "PostgreSQL", "Docker", "Redis", "Git", "CI/CD"],
        "jd_title": "Senior Python Backend Engineer",
        "jd_text": "We are seeking a Senior Python Backend Developer with 4+ years building high-throughput REST APIs using FastAPI, PostgreSQL, Docker, Redis, and cloud infrastructure.",
        "score": 93.5,
        "label": "Good Fit",
        "matched": ["Python", "FastAPI", "PostgreSQL", "Docker", "Redis", "Git"],
        "missing": ["AWS", "Kubernetes"],
        "explanation": "Candidate exhibits exceptional alignment with core backend stack. 4+ years of Python/FastAPI experience and proven database design skills make them a primary candidate.",
        "days_ago": 1,
    },
    {
        "filename": "Tran_Thi_B_Fullstack_React_Node.pdf",
        "skills": ["React", "JavaScript", "TypeScript", "Node.JS", "Express", "MongoDB", "HTML", "CSS"],
        "jd_title": "Fullstack Web Developer",
        "jd_text": "Looking for a Fullstack Developer proficient in React, Node.js, TypeScript, and MongoDB to join our agile product squad.",
        "score": 88.0,
        "label": "Good Fit",
        "matched": ["React", "JavaScript", "TypeScript", "Node.JS", "MongoDB"],
        "missing": ["GraphQL", "Next.js"],
        "explanation": "Strong frontend and intermediate backend skills align directly with the required modern JavaScript stack. High cultural and technical suitability.",
        "days_ago": 2,
    },
    {
        "filename": "Le_Van_C_Data_Scientist.pdf",
        "skills": ["Python", "Machine Learning", "Scikit-Learn", "Pandas", "NumPy", "SQL"],
        "jd_title": "Data Scientist & ML Engineer",
        "jd_text": "Requirements: Strong background in Python, Scikit-learn, PyTorch, predictive modeling, statistical analysis, and feature engineering for recruitment data.",
        "score": 86.2,
        "label": "Good Fit",
        "matched": ["Python", "Machine Learning", "Scikit-Learn", "Pandas", "NumPy", "SQL"],
        "missing": ["PyTorch", "MLflow"],
        "explanation": "Candidate demonstrates solid foundational ML knowledge with strong pandas/scikit-learn proficiency. Minor skill gap in MLOps tools can be bridged rapidly.",
        "days_ago": 3,
    },
    {
        "filename": "Pham_Minh_D_Junior_Java_Dev.pdf",
        "skills": ["Java", "Spring Boot", "MySQL", "Git"],
        "jd_title": "Mid-Level Java Engineer",
        "jd_text": "Seeking a Mid-Level Java Engineer with experience in Spring Boot, Microservices, Kafka, Redis, and Kubernetes.",
        "score": 64.5,
        "label": "Potential Fit",
        "matched": ["Java", "Spring Boot", "MySQL", "Git"],
        "missing": ["Kafka", "Microservices", "Kubernetes", "Redis"],
        "explanation": "Candidate possesses foundational Java and Spring Boot knowledge, but lacks hands-on distributed systems and Kafka streaming experience required for the mid-level role.",
        "days_ago": 4,
    },
    {
        "filename": "Hoang_Duc_E_DevOps_Specialist.pdf",
        "skills": ["Linux", "Docker", "Kubernetes", "AWS", "Terraform", "CI/CD", "Git"],
        "jd_title": "Cloud DevOps Engineer",
        "jd_text": "We need a Cloud DevOps Engineer to maintain our AWS Kubernetes clusters, manage CI/CD pipelines, and write Terraform infrastructure-as-code.",
        "score": 91.0,
        "label": "Good Fit",
        "matched": ["Linux", "Docker", "Kubernetes", "AWS", "Terraform", "CI/CD"],
        "missing": ["Monitoring/Prometheus"],
        "explanation": "Excellent infrastructure expertise. Thorough understanding of container orchestration and declarative cloud provisioning.",
        "days_ago": 5,
    },
    {
        "filename": "Vu_Thi_F_Chief_Accountant.pdf",
        "skills": ["Financial Reporting", "IFRS", "Excel", "Tax Audit", "SAP"],
        "jd_title": "Senior Python Backend Engineer",
        "jd_text": "We are seeking a Senior Python Backend Developer with 4+ years building high-throughput REST APIs using FastAPI, PostgreSQL, Docker, and Redis.",
        "score": 14.8,
        "label": "No Fit",
        "matched": ["General Qualifications"],
        "missing": ["Python", "FastAPI", "PostgreSQL", "Docker", "Redis"],
        "explanation": "Severe domain mismatch: Candidate profile is focused on corporate finance and accounting, whereas the target job requires software engineering and Python backend development.",
        "days_ago": 6,
    },
    {
        "filename": "Dang_Quoc_G_Marketing_Executive.pdf",
        "skills": ["SEO", "Content Marketing", "Google Analytics", "Social Media"],
        "jd_title": "Data Scientist & ML Engineer",
        "jd_text": "Requirements: Strong background in Python, Scikit-learn, PyTorch, predictive modeling, and statistical analysis.",
        "score": 18.2,
        "label": "No Fit",
        "matched": ["General Qualifications"],
        "missing": ["Python", "Machine Learning", "Scikit-Learn", "Pandas", "SQL"],
        "explanation": "Domain divergence: Marketing qualifications do not fulfill technical requirements for mathematical modeling and machine learning algorithms.",
        "days_ago": 7,
    },
    {
        "filename": "Doan_Thanh_H_QA_Automation.pdf",
        "skills": ["Python", "Selenium", "Pytest", "Postman", "Git", "CI/CD"],
        "jd_title": "Python Backend Engineer",
        "jd_text": "Seeking a Python Backend Engineer with FastAPI, SQL databases, and web services development skills.",
        "score": 58.7,
        "label": "Potential Fit",
        "matched": ["Python", "Git", "CI/CD"],
        "missing": ["FastAPI", "PostgreSQL", "Redis"],
        "explanation": "Strong programming logic and test automation mindset, but lacks production experience building backend web APIs and persistent data models.",
        "days_ago": 8,
    },
    {
        "filename": "Bui_Xuan_I_Senior_Frontend_Architect.pdf",
        "skills": ["React", "TypeScript", "Next.JS", "Redux", "GraphQL", "Tailwind CSS"],
        "jd_title": "Lead Frontend Architect",
        "jd_text": "Looking for a Lead Frontend Architect to design micro-frontends with React, Next.js, TypeScript, and state management at enterprise scale.",
        "score": 95.0,
        "label": "Good Fit",
        "matched": ["React", "TypeScript", "Next.JS", "Redux", "GraphQL"],
        "missing": ["WebAssembly"],
        "explanation": "Outstanding match: Deep expertise in enterprise frontend architecture, state patterns, and typed web applications.",
        "days_ago": 9,
    },
    {
        "filename": "Nguyen_Thu_K_Financial_Analyst.pdf",
        "skills": ["Excel", "Financial Modeling", "Power BI", "SQL"],
        "jd_title": "Senior Accountant & Financial Auditor",
        "jd_text": "Requirements: Financial reporting, IFRS standards, audit workflows, financial modeling, and tax compliance.",
        "score": 84.5,
        "label": "Good Fit",
        "matched": ["Financial Modeling", "Excel", "SQL"],
        "missing": ["IFRS Audit Certification"],
        "explanation": "Solid analytical and quantitative finance background. Candidate shows strong potential to excel in financial auditing responsibilities.",
        "days_ago": 10,
    },
]


def seed_database():
    """Insert pre-seeded records into SQLite."""
    print("Creating tables if not exists...")
    create_tables()

    db = SessionLocal()
    existing_count = db.query(MatchingResult).count()
    if existing_count >= 10:
        print(f"Database already contains {existing_count} matching records. Skipping duplicate seed.")
        db.close()
        return

    print(f"Seeding {len(DEMO_CANDIDATES)} realistic candidate matching records...")
    now = datetime.datetime.utcnow()

    for item in DEMO_CANDIDATES:
        timestamp = now - datetime.timedelta(days=item["days_ago"], hours=random.randint(1, 12))

        cv_rec = CVRecord(
            filename=item["filename"],
            raw_text=f"Candidate CV Content for {item['filename']}\nSkills: {', '.join(item['skills'])}",
            extracted_data={"skills": item["skills"]},
            created_at=timestamp,
        )
        db.add(cv_rec)
        db.flush()

        jd_rec = JDRecord(
            jd_text=item["jd_text"],
            processed_data={"required_skills": item["matched"] + item["missing"]},
            created_at=timestamp,
        )
        db.add(jd_rec)
        db.flush()

        res_rec = MatchingResult(
            cv_id=cv_rec.id,
            jd_id=jd_rec.id,
            matching_score=item["score"],
            compatibility_label=item["label"],
            matched_skills=item["matched"],
            missing_skills=item["missing"],
            llm_explanation=item["explanation"],
            llm_status="success" if item["score"] > 80 else "fallback",
            created_at=timestamp,
        )
        db.add(res_rec)

    db.commit()
    total = db.query(MatchingResult).count()
    db.close()
    print(f"[OK] Database seeded successfully! Total matching records now: {total}")


if __name__ == "__main__":
    seed_database()

