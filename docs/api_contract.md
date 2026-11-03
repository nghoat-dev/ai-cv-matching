# API Contract – AI CV-Job Matching

> Sprint 1 · Version 1.0.0

---

## Base URL

```
http://localhost:8000
```

---

## US-01: Schemas & Data Contracts

### CVUploadRequest (multipart/form-data)

| Field      | Type          | Constraints              | Description                        |
|------------|---------------|--------------------------|------------------------------------|
| `pdf_file` | `UploadFile`  | PDF only, max 5 MB       | Candidate's CV in PDF format       |
| `jd_text`  | `string`      | non-empty                | Job description text               |

### CVExtractionResult

| Field             | Type             | Nullable | Description                               |
|-------------------|------------------|----------|-------------------------------------------|
| `full_name`       | `string`         | ✓        | Candidate full name extracted from CV     |
| `email`           | `string`         | ✓        | Candidate email address                   |
| `skills`          | `list[string]`   | –        | List of extracted skills                  |
| `education`       | `list[object]`   | –        | Education history entries                 |
| `work_experience` | `list[object]`   | –        | Work experience entries                   |
| `raw_text`        | `string`         | –        | Full raw text extracted from PDF          |

### JDProcessingResult

| Field                | Type           | Nullable | Description                               |
|----------------------|----------------|----------|-------------------------------------------|
| `job_title`          | `string`       | –        | Inferred or explicit job title            |
| `required_skills`    | `list[string]` | –        | Skills listed as required in the JD       |
| `experience_level`   | `string`       | ✓        | Junior / Mid / Senior, if determinable    |
| `normalized_jd_text` | `string`       | –        | Cleaned and normalised JD text            |

### MatchingResponse

| Field                 | Type                                    | Constraints     | Description                                |
|-----------------------|-----------------------------------------|-----------------|--------------------------------------------|
| `matching_score`      | `float`                                 | 0.0 – 100.0     | Overall matching score                     |
| `compatibility_label` | `"Good Fit" \| "Potential Fit" \| "No Fit"` | –           | Human-readable compatibility bucket        |
| `matched_skills`      | `list[string]`                          | –               | Skills present in both CV and JD           |
| `missing_skills`      | `list[string]`                          | –               | JD-required skills absent from CV          |
| `llm_explanation`     | `string`                                | nullable        | LLM-generated explanation                  |
| `llm_status`          | `"success" \| "fallback"`               | –               | LLM call outcome                           |

> **Validation rule:** `matching_score` outside `[0.0, 100.0]` raises `ValidationError`.

### ErrorResponse

| Field        | Type     | Description                              |
|--------------|----------|------------------------------------------|
| `error_code` | `string` | Machine-readable code (e.g. `HTTP_400`)  |
| `message`    | `string` | Human-readable description               |
| `details`    | `object` | Optional additional context              |

---

## Endpoints

### `GET /health`

Liveness probe.

**Response 200**
```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

---

### `GET /api/v1/info`

Returns descriptive API metadata.

**Response 200**
```json
{
  "name": "AI CV-Job Matching API",
  "version": "1.0.0",
  "description": "...",
  "endpoints": { ... }
}
```

---

### `POST /api/v1/match`

Upload a CV and job description; receive a matching result.

**Request** – `multipart/form-data`

| Part       | Content-Type      | Notes               |
|------------|-------------------|---------------------|
| `pdf_file` | `application/pdf` | Max 5 MB            |
| `jd_text`  | `text/plain`      | Non-empty string    |

**Response 200** – `MatchingResponse`
```json
{
  "matching_score": 72.5,
  "compatibility_label": "Potential Fit",
  "matched_skills": ["Python", "Machine Learning", "SQL"],
  "missing_skills": ["Kubernetes", "Spark"],
  "llm_explanation": "...",
  "llm_status": "fallback"
}
```

**Response 400** – `ErrorResponse` (invalid file type or size)

**Response 422** – `ErrorResponse` (validation failure)

**Response 500** – `ErrorResponse` (unexpected server error)

---

## Compatibility Labels

| Label           | Score Range  |
|-----------------|--------------|
| Good Fit        | ≥ 70.0       |
| Potential Fit   | 40.0 – 69.9  |
| No Fit          | < 40.0       |

---

## LLM Status Values

| Value      | Meaning                                            |
|------------|----------------------------------------------------|
| `success`  | LLM generated the explanation successfully         |
| `fallback` | LLM call failed; default message returned instead  |

---

## Error Codes

| Code                   | HTTP Status | Trigger                                      |
|------------------------|-------------|----------------------------------------------|
| `BAD_REQUEST`          | 400         | Invalid file type / oversized file           |
| `VALIDATION_ERROR`     | 422         | Pydantic schema validation failure           |
| `LLM_AUTH_ERROR`       | –           | LLM API key invalid (internal, logged)       |
| `INTERNAL_SERVER_ERROR`| 500         | Unhandled server exception                   |
