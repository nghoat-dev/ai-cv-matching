# Sprint 2 Enhanced Model Evaluation & Comparison Report (US-24)

## 1. Executive Summary
- **Sprint Goal:** Enhance ML matching pipeline to exceed Sprint 1 baseline performance on held-out test split (US-17, US-24).
- **Model Type:** Tuned Logistic Regression with Minority-Boosted Class Weights (L-BFGS, C=2.8).
- **Feature Space:** Shared TF-IDF (20,000 features, 1-2 ngrams) + Pairwise Cosine, Overlap, and Length Interactions.
- **Evaluation Set:** 18,738 strictly held-out test samples (identical to Sprint 1 evaluation, zero leakage).

## 2. Comparative Performance (Sprint 1 vs Sprint 2)
| Metric | Sprint 1 Baseline (v1) | Sprint 2 Enhanced (v2) | Improvement / Delta |
|---|---|---|---|
| **Macro F1-Score** | 67.89% | **71.04%** | **+3.15%** |
| **Overall Accuracy** | 77.15% | **82.29%** | **+5.14%** |
| **Weighted F1-Score** | 78.77% | **82.35%** | **+3.58%** |
| **Macro Precision** | 63.85% | **69.96%** | **+6.11%** |
| **Macro Recall** | 76.53% | **72.44%** | **-4.09%** |

## 3. Per-Class Performance (Sprint 2 v2)
| Class | Precision | Recall | F1-Score | Support |
|---|---|---|---|---|
| **No Fit (0)** | 0.9084 | 0.9007 | 0.9045 | 13746 |
| **Potential Fit (1)** | 0.5939 | 0.5678 | 0.5805 | 3498 |
| **Good Fit (2)** | 0.5966 | 0.7048 | 0.6462 | 1494 |

## 4. Confusion Matrix (Sprint 2 v2)
```
Predicted ->       No Fit    Potential Fit    Good Fit
Actual:
No Fit (0):         12381           1057         308
Potential Fit (1):    1108           1986         404
Good Fit (2):         140            301        1053
```

## 5. Acceptance Criteria Verification
- **US17-AC01 (Hyperparameter Tuning):** C parameter calibrated to 2.8 with minority-boosted weights.
- **US17-AC02 (Model Serialization):** Serialized to `models/advanced_pipeline_v2.joblib` with full metadata and score function.
- **US18-AC01 (Deterministic Scoring Engine):** Scoring engine `compute_matching_score_v2` maps class probabilities to [0.0, 100.0] monotonically.
- **US24-AC01 (Fair Comparative Evaluation):** Both models evaluated on the exact same 18,738 held-out test split.
- **US24-AC02 (F1 Target Achievement):** Enhanced model demonstrates superior Macro F1 performance.
