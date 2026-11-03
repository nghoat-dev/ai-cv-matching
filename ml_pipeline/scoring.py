"""
Scoring functions for CV-Job Matching.

Deterministic mapping from class probabilities and cosine similarity to calibrated [0.0, 100.0] scale.
"""

from __future__ import annotations

import numpy as np


def compute_matching_score(
    probabilities: np.ndarray, cosine_similarities: np.ndarray | None = None
) -> np.ndarray:
    """Baseline v1 scoring formula."""
    p_no_fit = probabilities[:, 0]
    p_potential = probabilities[:, 1]
    p_good_fit = probabilities[:, 2]

    if cosine_similarities is not None:
        score = p_good_fit * 70.0 + p_potential * 40.0 + cosine_similarities * 30.0
    else:
        score = p_good_fit * 80.0 + p_potential * 30.0 + (1.0 - p_no_fit) * 20.0 * 0.5

    return np.clip(score, 0.0, 100.0)


def compute_matching_score_v2(
    probabilities: np.ndarray, cosine_similarities: np.ndarray | None = None
) -> np.ndarray:
    """
    Sprint 2 & 3 enhanced scoring engine.
    Calibrated multi-class weighted scoring.
    """
    p_no_fit = probabilities[:, 0]
    p_potential = probabilities[:, 1]
    p_good_fit = probabilities[:, 2]

    # Weighted combination: Good Fit rewards heavily, No Fit penalizes heavily
    raw_score = (p_good_fit * 90.0) + (p_potential * 55.0) + ((1.0 - p_no_fit) * 10.0)

    if cosine_similarities is not None:
        raw_score = 0.75 * raw_score + 0.25 * (cosine_similarities * 100.0)

    return np.clip(raw_score, 0.0, 100.0)

