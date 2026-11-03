"""
CV & JD Multi-Dimensional Extraction Service.

Extracts structured sections from CV PDF documents and Job Descriptions using
PyMuPDF, rule-based heuristics, lookaround token extractors, date-range calculators,
and optional LLM structured JSON output.
"""

from __future__ import annotations

import datetime
import logging
import re
from typing import Any

import fitz  # PyMuPDF

from backend.app.schemas import CVExtractedData, JDExtractedData
from backend.app.services.llm_service import LLMService

logger = logging.getLogger(__name__)

CURRENT_YEAR = datetime.datetime.now().year
CURRENT_MONTH = datetime.datetime.now().month

# 1. Tech Skills Taxonomy (Canonical Name -> List of aliases)
TECH_SKILLS_TAXONOMY: dict[str, list[str]] = {
    "Python": ["python"],
    "JavaScript": ["javascript", "js"],
    "TypeScript": ["typescript", "ts"],
    "React": ["react", "reactjs", "react.js"],
    "Node.js": ["node.js", "nodejs", "node"],
    "FastAPI": ["fastapi"],
    "Django": ["django"],
    "Flask": ["flask"],
    "Java": ["java"],
    "Spring Boot": ["spring boot", "spring"],
    "C++": ["c++"],
    "C#": ["c#"],
    ".NET": [".net", "dotnet", "asp.net"],
    "Go": ["go", "golang"],
    "Rust": ["rust"],
    "PHP": ["php", "laravel"],
    "Ruby": ["ruby", "rails"],
    "SQL": ["sql", "mysql", "postgresql", "postgres", "sqlite", "sql server", "oracle"],
    "MongoDB": ["mongodb", "mongo"],
    "Redis": ["redis"],
    "Elasticsearch": ["elasticsearch"],
    "Docker": ["docker"],
    "Kubernetes": ["kubernetes", "k8s"],
    "AWS": ["aws", "amazon web services"],
    "Azure": ["azure"],
    "GCP": ["gcp", "google cloud"],
    "Git": ["git", "github", "gitlab"],
    "CI/CD": ["ci/cd", "jenkins", "gitlab ci", "github actions"],
    "Linux": ["linux", "ubuntu"],
    "Machine Learning": ["machine learning", "ml"],
    "Scikit-Learn": ["scikit-learn", "sklearn"],
    "Deep Learning": ["deep learning"],
    "PyTorch": ["pytorch"],
    "TensorFlow": ["tensorflow", "tf"],
    "Computer Vision": ["computer vision", "opencv"],
    "NLP": ["nlp", "natural language processing", "llm", "large language model", "transformers"],
    "Pandas": ["pandas"],
    "NumPy": ["numpy"],
    "Spark": ["spark", "pyspark", "hadoop"],
    "Power BI": ["power bi"],
    "Tableau": ["tableau"],
}

# 2. Other Requirements & Qualifications Taxonomy
OTHER_REQUIREMENTS_TAXONOMY: dict[str, list[str]] = {
    # Degree / Education
    "Bachelor's Degree": ["bachelor", "b.s", "b.sc", "b.eng", "university degree", "graduated", "cử nhân", "kỹ sư"],
    "Master's Degree": ["master", "m.s", "m.sc", "m.eng", "mba", "thạc sĩ"],
    "Doctorate / PhD": ["phd", "doctorate", "tiến sĩ"],
    "CS/IT Major": ["computer science", "information technology", "software engineering", "data science", "cntt", "khoa học máy tính", "công nghệ thông tin"],
    # Languages & Certifications
    "English Proficiency": ["english", "toeic", "ielts", "toefl", "fluent in english", "good communication in english", "tiếng anh"],
    "Japanese (JLPT)": ["japanese", "jlpt", "n1", "n2", "n3", "tiếng nhật"],
    "Cloud/IT Certification": ["aws certified", "azure certified", "gcp certified", "pmp", "istqb", "ccna", "ccnp", "deep learning specialization", "cka"],
    # Soft skills & Methodologies
    "Agile / Scrum": ["agile", "scrum", "kanban", "jira", "sprint"],
    "Problem Solving": ["problem solving", "problem-solving", "analytical thinking", "troubleshooting", "giải quyết vấn đề"],
    "Teamwork & Communication": ["teamwork", "team player", "communication skills", "cross-functional", "collaboration", "giao tiếp", "làm việc nhóm"],
    "System Design / Architecture": ["system design", "microservices", "scalable", "architecture", "rest api", "restful", "thiết kế hệ thống"],
    "Testing & Debugging": ["unit test", "integration test", "pytest", "jest", "debugging", "qa", "ci/cd"],
}

DEGREE_HIERARCHY: dict[str, int] = {
    "Doctorate / PhD": 4,
    "Master's Degree": 3,
    "Bachelor's Degree": 2,
    "Associate": 1,
}

# Categorized dictionary mapping for legacy consumers
SKILL_TAXONOMY: dict[str, list[str]] = {
    "Programming Languages": ["python", "java", "c++", "c#", ".net", "javascript", "typescript", "go", "rust", "php", "ruby"],
    "Frameworks & Libraries": ["react", "node.js", "fastapi", "django", "flask", "spring boot", "pytorch", "tensorflow", "scikit-learn", "pandas", "numpy"],
    "Databases & Caches": ["sql", "postgresql", "mysql", "mongodb", "redis", "elasticsearch", "sqlite"],
    "Cloud & DevOps": ["docker", "kubernetes", "aws", "azure", "gcp", "git", "ci/cd", "jenkins", "linux"],
    "Data & AI": ["machine learning", "deep learning", "nlp", "computer vision", "llm", "spark"],
}

ALL_TAXONOMY_SKILLS = [s for sublist in SKILL_TAXONOMY.values() for s in sublist]

EXCLUDED_NAME_TERMS = {
    "ha noi", "hanoi", "ho chi minh", "ho chi minh city", "tp ho chi minh",
    "hcm", "da nang", "da lat", "can tho", "hai phong", "viet nam", "vietnam",
    "curriculum", "vitae", "resume", "page", "developer", "engineer", "education",
    "skills", "experience", "work", "objective", "summary", "profile", "projects",
    "certifications", "interests", "references", "activities", "awards", "languages",
    "contact", "information", "university", "college", "school", "machine", "learning",
    "deep", "data", "software", "analysis", "processing", "structures", "algorithms",
    "award", "club", "co-leader", "distinction", "specialization", "bachelor", "master",
}


def extract_taxonomy_items(text: str, taxonomy: dict[str, list[str]]) -> list[str]:
    """
    Bắt các kỹ năng hoặc yêu cầu dựa trên từ điển đồng nghĩa.
    Sử dụng lookaround (?<![a-z0-9]) ... (?![a-z0-9]) để bảo toàn an toàn các ký tự C++, C#, .NET.
    """
    text_lower = text.lower()
    found: list[str] = []
    for canonical, aliases in taxonomy.items():
        for alias in aliases:
            pattern = r"(?<![a-z0-9])" + re.escape(alias) + r"(?![a-z0-9])"
            if re.search(pattern, text_lower):
                found.append(canonical)
                break
    return found


def extract_experience_years(text: str, is_jd: bool = False) -> float:
    """
    Trích xuất số năm kinh nghiệm:
    - Với JD: Bắt '2+ years of experience', 'at least 3 years', hoặc trả về 0.0 cho Fresher/Intern.
    - Với CV: Bắt câu ghi trực tiếp LẪN tính tổng thời gian từ các mốc '06/2023 - Present', '2022 - 2024'.
    """
    text_lower = text.lower()

    if is_jd:
        if re.search(r"\b(intern|internship|fresher|entry[- ]level|no experience)\b", text_lower):
            explicit_yrs = re.findall(r"(\d+(?:\.\d+)?)\s*\+?\s*(?:-\s*\d+\s*)?years?\s+(?:of\s+)?experience", text_lower)
            if not explicit_yrs:
                return 0.0

    # 1. Tìm câu trực tiếp: "5 years of experience", "over 3 years..."
    explicit_matches = re.findall(
        r"(?:at least|minimum|over|more than|tối thiểu)?\s*(\d+(?:\.\d+)?)\s*(?:\+|-\s*\d+)?\s*(?:years?|năm)\s+(?:of\s+)?(?:work\s+|practical\s+|relevant\s+)?experience",
        text_lower,
    )
    explicit_years = max([float(m) for m in explicit_matches], default=0.0)
    if is_jd:
        return explicit_years

    # 2. Với CV: Bắt các khoảng thời gian (hỗ trợ cả năm 1990 tới nay)
    date_range_pattern = re.compile(
        r"(?:(0?[1-9]|1[0-2])[/.-])?(19\d{2}|20\d{2})\s*(?:-|–|—|to)\s*(?:(0?[1-9]|1[0-2])[/.-])?(19\d{2}|20\d{2}|present|current|now|hiện tại)",
        re.IGNORECASE,
    )

    intervals: list[tuple[float, float]] = []
    for match in date_range_pattern.finditer(text_lower):
        m1, y1, m2, y2 = match.groups()
        start_val = int(y1) + ((int(m1) - 1) / 12.0 if m1 else 0.0)

        if y2 in ("present", "current", "now", "hiện tại"):
            end_val = CURRENT_YEAR + ((CURRENT_MONTH - 1) / 12.0)
        else:
            end_val = int(y2) + ((int(m2) - 1) / 12.0 if m2 else 11.0 / 12.0)

        if 0.1 <= (end_val - start_val) <= 35.0:
            intervals.append((start_val, end_val))

    # Gộp các khoảng thời gian giao nhau (Interval merging)
    calculated_years = 0.0
    if intervals:
        intervals.sort(key=lambda x: x[0])
        merged = [intervals[0]]
        for start, end in intervals[1:]:
            prev_start, prev_end = merged[-1]
            if start <= prev_end:
                merged[-1] = (prev_start, max(prev_end, end))
            else:
                merged.append((start, end))
        calculated_years = round(sum(e - s for s, e in merged), 1)

    return max(explicit_years, calculated_years)


# Aliases for backward compatibility
parse_experience_years = extract_experience_years
parse_jd_min_experience = lambda text: extract_experience_years(text, is_jd=True)


def extract_experience_and_responsibility_lines(text: str) -> list[str]:
    """
    Lọc ra các câu mô tả kinh nghiệm hoặc trách nhiệm dựa trên Action Verbs,
    bảo toàn ranh giới câu (tránh bẻ gãy Node.js hay số thập phân 3.5).
    """
    action_pattern = re.compile(
        r"\b(developed|built|designed|implemented|managed|led|created|optimized|maintained|"
        r"collaborated|deployed|integrated|analyzed|trained|engineered|participated|"
        r"phát triển|thiết kế|xây dựng|triển khai|tối ưu|vận hành|chịu trách nhiệm|"
        r"experience in|responsible for|duties include|work with|working on|familiar with)\b",
        re.IGNORECASE,
    )
    raw_lines = re.split(r"\n+|(?<!\b[a-zA-Z0-9])\.\s+", text)
    cleaned = [line.strip(" •-*▪\t\r") for line in raw_lines if len(line.strip()) >= 20]
    matched = [line for line in cleaned if action_pattern.search(line)]
    return matched[:25] if matched else cleaned[:15]


def segment_cv_sections(raw_text: str) -> dict[str, list[str]]:
    """Segment raw CV text into logical sections based on common headers."""
    headers = [
        ("EXPERIENCE", re.compile(r"^(work experience|professional experience|employment history|experience|kinh nghiệm làm việc|kinh nghiệm)", re.I)),
        ("PROJECTS", re.compile(r"^(projects|key projects|side projects|dự án)", re.I)),
        ("EDUCATION", re.compile(r"^(education|academic background|học vấn|bằng cấp|trình độ)", re.I)),
        ("SKILLS", re.compile(r"^(technical skills|skills|core competencies|kỹ năng|chuyên môn)", re.I)),
        ("CERTIFICATIONS", re.compile(r"^(certifications|certificates|honors & awards|awards|chứng chỉ)", re.I)),
        ("OBJECTIVE", re.compile(r"^(objective|career objective|professional summary|summary|mục tiêu nghề nghiệp|mục tiêu)", re.I)),
        ("ACTIVITIES", re.compile(r"^(activities|interests|references|hoạt động|sở thích)", re.I)),
    ]

    sections: dict[str, list[str]] = {"GENERAL": []}
    current_sec = "GENERAL"

    for line in raw_text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        matched_sec = None
        for sec_name, pat in headers:
            if pat.match(stripped):
                matched_sec = sec_name
                break
        if matched_sec:
            current_sec = matched_sec
            sections.setdefault(current_sec, [])
        else:
            sections.setdefault(current_sec, []).append(stripped)

    return sections


def segment_jd_sections(jd_text: str) -> dict[str, list[str]]:
    """Segment Job Description text into logical sections."""
    headers = [
        ("RESPONSIBILITIES", re.compile(r"^(responsibilities|job responsibilities|duties|what you'?ll do|key tasks|mô tả công việc|trách nhiệm|vai trò)", re.I)),
        ("REQUIREMENTS", re.compile(r"^(requirements|job requirements|qualifications|what we'?re looking for|skills required|yêu cầu công việc|yêu cầu)", re.I)),
        ("BENEFITS", re.compile(r"^(benefits|what we offer|perks|quyền lợi|chế độ)", re.I)),
    ]

    sections: dict[str, list[str]] = {"GENERAL": []}
    current_sec = "GENERAL"

    for line in jd_text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        matched_sec = None
        for sec_name, pat in headers:
            if pat.match(stripped):
                matched_sec = sec_name
                break
        if matched_sec:
            current_sec = matched_sec
            sections.setdefault(current_sec, [])
        else:
            sections.setdefault(current_sec, []).append(stripped)

    return sections


class CVExtractor:
    """Extracts multi-dimensional structured entities and sections from candidate CVs and JDs."""

    def __init__(self) -> None:
        self.llm_service = LLMService()

    def extract_text_from_bytes(self, pdf_bytes: bytes, filename: str = "") -> str:
        """Extract plain text from in-memory PDF bytes using PyMuPDF."""
        raw_text = ""
        try:
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            for page_num in range(len(doc)):
                page = doc[page_num]
                raw_text += page.get_text() + "\n"
            doc.close()
        except Exception as exc:
            logger.warning("PyMuPDF failed to extract text from '%s': %s", filename, exc)
        return raw_text.strip()

    def _extract_name_from_pdf_spans(self, pdf_bytes: bytes) -> str | None:
        """Heuristically extract candidate name using font-size hierarchy from the first PDF page."""
        try:
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            if len(doc) == 0:
                doc.close()
                return None
            first_page = doc[0]
            blocks = first_page.get_text("dict").get("blocks", [])
            spans: list[tuple[float, str]] = []
            for b in blocks:
                if "lines" in b:
                    for l in b["lines"]:
                        for s in l.get("spans", []):
                            txt = s.get("text", "").strip()
                            if txt:
                                spans.append((float(s.get("size", 0.0)), txt))
            doc.close()

            spans.sort(key=lambda x: x[0], reverse=True)
            for sz, txt in spans:
                if sz < 12.0:
                    break
                clean = re.sub(r"^[\d\.\-\•\*\s]+", "", txt).strip()
                words = clean.split()
                if 2 <= len(words) <= 5 and all(w.isalpha() and w[0].isupper() for w in words):
                    clean_lower = clean.lower()
                    if clean_lower not in EXCLUDED_NAME_TERMS and not any(t in clean_lower for t in EXCLUDED_NAME_TERMS):
                        return clean
        except Exception as exc:
            logger.debug("Failed font-size span name extraction: %s", exc)
        return None

    def extract_cv_structured(
        self, raw_text: str, pdf_bytes: bytes | None = None
    ) -> CVExtractedData:
        """
        Multi-dimensional extraction for CVs.
        Uses LLM JSON extraction when configured, falling back to rule-based & section parser.
        """
        # 1. Candidate Full Name, Email, Phone
        full_name = self._extract_name_from_pdf_spans(pdf_bytes) if pdf_bytes else None
        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]

        if not full_name:
            for line in lines:
                clean = re.sub(r"^[\d\.\-\•\*\s]+", "", line).strip()
                words = clean.split()
                if 2 <= len(words) <= 4 and all(w.isalpha() and w[0].isupper() for w in words):
                    clean_lower = clean.lower()
                    if clean_lower not in EXCLUDED_NAME_TERMS and not any(kw in clean_lower for kw in EXCLUDED_NAME_TERMS):
                        full_name = clean
                        break

        email = None
        email_match = re.search(r"[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}", raw_text)
        if email_match:
            email = email_match.group(0).lower()

        phone = None
        phone_match = re.search(r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", raw_text)
        if phone_match:
            phone = phone_match.group(0)

        # 2. Try LLM Hybrid Extraction
        llm_data = self.llm_service.extract_cv_with_llm(raw_text)
        if llm_data:
            return CVExtractedData(
                full_name=full_name,
                email=email,
                phone=phone,
                technical_skills=llm_data.get("technical_skills", []),
                total_experience_years=float(llm_data.get("total_experience_years", 0.0)),
                experience_descriptions=llm_data.get("experience_descriptions", []),
                education_level=llm_data.get("education_level"),
                other_qualifications=llm_data.get("other_qualifications", []),
                raw_text=raw_text,
            )

        # 3. Rule-Based & Section Segmentation Fallback
        sections = segment_cv_sections(raw_text)
        exp_lines = sections.get("EXPERIENCE", []) + sections.get("PROJECTS", [])
        exp_text = "\n".join(exp_lines)

        # Total experience years
        if exp_text:
            total_exp = extract_experience_years(exp_text, is_jd=False)
        else:
            total_exp = extract_experience_years(raw_text, is_jd=False)

        # Technical skills extraction using exact lookaround taxonomy
        extracted_tech = extract_taxonomy_items(raw_text, TECH_SKILLS_TAXONOMY)

        # Experience descriptions (actionable lines)
        experience_descriptions = extract_experience_and_responsibility_lines(exp_text or raw_text)

        # Other qualifications (education, languages, soft skills, certs)
        other_quals = extract_taxonomy_items(raw_text, OTHER_REQUIREMENTS_TAXONOMY)

        # Highest education level
        education_level = None
        for deg in ["Doctorate / PhD", "Master's Degree", "Bachelor's Degree"]:
            if deg in other_quals:
                education_level = deg.replace("'s Degree", "").replace("Doctorate / ", "")
                break

        return CVExtractedData(
            full_name=full_name,
            email=email,
            phone=phone,
            technical_skills=extracted_tech,
            total_experience_years=total_exp,
            experience_descriptions=experience_descriptions,
            education_level=education_level,
            other_qualifications=other_quals,
            raw_text=raw_text,
        )

    def extract_jd_structured(self, jd_text: str) -> JDExtractedData:
        """
        Multi-dimensional extraction for Job Descriptions.
        Uses LLM JSON extraction when configured, falling back to rule-based & section parser.
        """
        # 1. Try LLM Hybrid Extraction
        llm_data = self.llm_service.extract_jd_with_llm(jd_text)
        if llm_data:
            return JDExtractedData(
                job_title=llm_data.get("job_title"),
                required_technical_skills=llm_data.get("required_technical_skills", []),
                min_experience_years=float(llm_data.get("min_experience_years", 0.0)),
                job_responsibilities=llm_data.get("job_responsibilities", []),
                required_education=llm_data.get("required_education"),
                other_requirements=llm_data.get("other_requirements", []),
                normalized_jd_text=jd_text,
            )

        # 2. Rule-Based & Section Segmentation Fallback
        sections = segment_jd_sections(jd_text)

        # Job title heuristic from first lines
        job_title = None
        for line in jd_text.splitlines()[:4]:
            stripped = line.strip()
            if 5 <= len(stripped) <= 60 and not stripped.endswith(":"):
                job_title = stripped
                break

        # Required technical skills via lookaround taxonomy
        required_tech = extract_taxonomy_items(jd_text, TECH_SKILLS_TAXONOMY)

        # Min experience years
        req_lines = sections.get("REQUIREMENTS", [])
        req_text = "\n".join(req_lines) if req_lines else jd_text
        min_exp = extract_experience_years(req_text, is_jd=True)
        if min_exp == 0.0:
            min_exp = extract_experience_years(jd_text, is_jd=True)

        # Job responsibilities
        resp_lines = sections.get("RESPONSIBILITIES", [])
        resp_text = "\n".join(resp_lines) if resp_lines else jd_text
        job_responsibilities = extract_experience_and_responsibility_lines(resp_text)

        # Other requirements (soft skills, languages, certs, methods)
        other_reqs = extract_taxonomy_items(jd_text, OTHER_REQUIREMENTS_TAXONOMY)

        # Required education
        required_edu = None
        for deg in ["Doctorate / PhD", "Master's Degree", "Bachelor's Degree"]:
            if deg in other_reqs:
                required_edu = deg.replace("'s Degree", "").replace("Doctorate / ", "")
                break

        return JDExtractedData(
            job_title=job_title,
            required_technical_skills=required_tech,
            min_experience_years=min_exp,
            job_responsibilities=job_responsibilities,
            required_education=required_edu,
            other_requirements=other_reqs,
            normalized_jd_text=jd_text,
        )

    def extract_structured_data(
        self, raw_text: str, pdf_bytes: bytes | None = None
    ) -> dict[str, Any]:
        """Backward-compatible extraction dictionary populated with multi-dimensional data."""
        cv_data = self.extract_cv_structured(raw_text, pdf_bytes)

        # Categorize skills for legacy callers
        skills_by_category: dict[str, list[str]] = {}
        for cat, skills in SKILL_TAXONOMY.items():
            found = [s for s in cv_data.technical_skills if s.lower() in [sk.lower() for sk in skills]]
            if found:
                skills_by_category[cat] = found

        education_entries = (
            [{"entry": f"{cv_data.education_level} Degree"}] if cv_data.education_level else []
        )
        work_entries = [{"entry": desc} for desc in cv_data.experience_descriptions]

        return {
            "full_name": cv_data.full_name,
            "email": cv_data.email,
            "phone": cv_data.phone,
            "skills": cv_data.technical_skills,
            "technical_skills": cv_data.technical_skills,
            "skills_by_category": skills_by_category,
            "total_experience_years": cv_data.total_experience_years,
            "experience_descriptions": cv_data.experience_descriptions,
            "education_level": cv_data.education_level,
            "other_qualifications": cv_data.other_qualifications,
            "education": education_entries,
            "work_experience": work_entries,
            "raw_text": raw_text,
        }
