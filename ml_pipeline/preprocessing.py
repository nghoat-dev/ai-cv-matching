"""
US-08: Preprocess and Normalize Raw Resume and JD Text.
Stateless, reusable module for both training and inference.
"""
import re
import unicodedata
import logging

logger = logging.getLogger(__name__)

# Technical tokens to preserve (regex pattern -> clean lowercase output)
TECH_TOKEN_PATTERNS = [
    (r'(?i)\bc\+\+(?!\w)', 'c++'),
    (r'(?i)\bc#(?!\w)', 'c#'),
    (r'(?i)\.net(?!\w)', '.net'),
    (r'(?i)\bnode\.js(?!\w)', 'node.js'),
    (r'(?i)\breact\.js(?!\w)', 'react.js'),
    (r'(?i)\bci/cd(?!\w)', 'ci/cd'),
    (r'(?i)\baws\s+s3(?!\w)', 'aws s3'),
    (r'(?i)\basp\.net(?!\w)', 'asp.net'),
    (r'(?i)\bvue\.js(?!\w)', 'vue.js'),
    (r'(?i)\bexpress\.js(?!\w)', 'express.js'),
]


def _strip_html(text: str) -> str:
    """Remove HTML tags, replacing with space to avoid word merging."""
    return re.sub(r'<[^>]+>', ' ', text)


def _strip_markdown_urls(text: str) -> str:
    """Remove markdown links and bare URLs."""
    text = re.sub(r'\[([^\]]*)\]\([^\)]*\)', r'\1', text)
    text = re.sub(r'https?://\S+', ' ', text)
    text = re.sub(r'www\.\S+', ' ', text)
    return text


def _strip_email(text: str) -> str:
    """Remove email addresses."""
    return re.sub(r'\b[\w.+-]+@[\w-]+\.[a-z]{2,}\b', ' ', text, flags=re.IGNORECASE)


def _preserve_tech_tokens(text: str) -> tuple:
    """Protect technical tokens with safe placeholder markers."""
    placeholders = {}
    placeholder_text = text
    for i, (pattern, replacement) in enumerate(TECH_TOKEN_PATTERNS):
        placeholder = f'__techtoken{i}__'
        new_text, count = re.subn(pattern, f' {placeholder} ', placeholder_text)
        if count > 0:
            placeholders[placeholder] = replacement
            placeholder_text = new_text
    return placeholder_text, placeholders


def _restore_tech_tokens(text: str, placeholders: dict) -> str:
    """Restore preserved technical tokens from placeholders."""
    for placeholder, token in placeholders.items():
        text = text.replace(placeholder, token)
    return text


def normalize_text(text: str) -> str:
    """
    Normalize resume or JD text for ML processing.
    
    - Strips HTML tags (with space separation)
    - Removes URLs and emails
    - NFKC Unicode normalization
    - Preserves technical skill tokens (C++, C#, .NET, Node.js, CI/CD, etc.)
    - Lowercase conversion
    - Collapses whitespace
    """
    if not text or not isinstance(text, str):
        return ''
    
    # Strip HTML first (replace tags with space)
    text = _strip_html(text)
    
    # Remove URLs and emails
    text = _strip_markdown_urls(text)
    text = _strip_email(text)
    
    # Unicode NFKC normalization
    text = unicodedata.normalize('NFKC', text)
    
    # Preserve technical tokens with alphanumeric placeholders
    text, placeholders = _preserve_tech_tokens(text)
    
    # Lowercase
    text = text.lower()
    
    # Remove punctuation (keep letters, digits, whitespace, and underscore for placeholders)
    text = re.sub(r'[^\w\s]', ' ', text)
    
    # Restore technical tokens
    text = _restore_tech_tokens(text, placeholders)
    
    # Collapse whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text
    
    return text


def _normalize_batch(texts: list) -> list:
    """Helper for parallel processing of text batches."""
    return [normalize_text(t) for t in texts]


def preprocess_dataframe(df, resume_col='resume', jd_col='jd'):
    """Apply normalize_text to resume and jd columns using multi-core parallel processing."""
    import pandas as pd
    import os
    from concurrent.futures import ProcessPoolExecutor
    
    df = df.copy()
    n_workers = min(os.cpu_count() or 4, 8)
    logger.info(f"Normalizing texts using {n_workers} worker processes...")
    
    # Process resume column
    resumes = df[resume_col].fillna('').astype(str).tolist()
    chunk_size = max(1, len(resumes) // (n_workers * 2))
    resume_chunks = [resumes[i:i + chunk_size] for i in range(0, len(resumes), chunk_size)]
    
    with ProcessPoolExecutor(max_workers=n_workers) as executor:
        results = list(executor.map(_normalize_batch, resume_chunks))
    df[resume_col] = [item for sublist in results for item in sublist]
    
    # Process jd column
    jds = df[jd_col].fillna('').astype(str).tolist()
    jd_chunks = [jds[i:i + chunk_size] for i in range(0, len(jds), chunk_size)]
    
    with ProcessPoolExecutor(max_workers=n_workers) as executor:
        results = list(executor.map(_normalize_batch, jd_chunks))
    df[jd_col] = [item for sublist in results for item in sublist]
    
    # Drop records that became empty after normalization
    initial = len(df)
    min_len = 15
    mask = (df[resume_col].str.len() >= min_len) & (df[jd_col].str.len() >= min_len)
    df = df[mask].reset_index(drop=True)
    dropped = initial - len(df)
    if dropped > 0:
        logger.info(f"Dropped {dropped} records that became too short after normalization")
    
    logger.info(f"Preprocessed DataFrame ready: {len(df)} rows")
    return df


if __name__ == "__main__":
    # Unit tests
    test_cases = [
        ("Senior Developer: C++, C#, .NET Core, Node.js & CI/CD!\n\nExperience: 5+ yrs", 
         ['c++', 'c#', '.net', 'node.js', 'ci/cd']),
        ("<p>Python</p><p>Developer</p>", ['python', 'developer']),
    ]
    
    print("Running preprocessing unit tests...")
    for text, expected_tokens in test_cases:
        result = normalize_text(text)
        print(f"Input: {text[:50]}...")
        print(f"Output: {result[:100]}")
        for token in expected_tokens:
            assert token in result, f"Token '{token}' not found in output: {result}"
        # Check no word merging
        if 'python' in expected_tokens and 'developer' in expected_tokens:
            assert 'pythondeveloper' not in result, "Words incorrectly merged!"
        print(f"  [OK] All {len(expected_tokens)} tokens verified")
    print("All unit tests passed!")
