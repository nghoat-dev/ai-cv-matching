# Sprint 1 Baseline Model Evaluation Report

## 1. Executive Summary
- **Model Type:** Baseline Logistic Regression (balanced class weights, L-BFGS)
- **Features:** Shared TF-IDF (20,000 max features, 1-2 ngrams) + 3 Pairwise Signals
- **Evaluation Split:** Held-out test set strictly unseen during training (18,738 rows)
- **Zero Leakage:** Verified 0 overlapping pairs between train and test splits

## 2. Core Metrics
| Metric | Value |
|---|---|
| **Overall Accuracy** | 77.15% |
| **Macro Precision** | 64.16% |
| **Macro Recall** | 75.62% |
| **Macro F1-Score** | 67.89% |
| **Weighted F1-Score** | 78.77% |

## 3. Per-Class Performance
| Class | Precision | Recall | F1-Score | Support |
|---|---|---|---|---|
| **No Fit (0)** | 0.9449 | 0.7946 | 0.8633 | 13746 |
| **Potential Fit (1)** | 0.4974 | 0.6641 | 0.5688 | 3498 |
| **Good Fit (2)** | 0.4825 | 0.8099 | 0.6047 | 1494 |

## 4. Confusion Matrix
```
Predicted ->     No Fit  Potential Fit  Good Fit
Actual:
No Fit (0):        10923           2111       712
Potential Fit (1):    589           2323       586
Good Fit (2):         48            236      1210
```

## 5. Error Analysis & Baseline Weaknesses
Top sample error patterns identified:

### Error Case 1: Actual `Potential Fit` -> Predicted `Good Fit`
- **Resume snippet:** summarystrong it experience in aws cloud computing bigdata data warehousing strong business domain knowledge in sales segmentation territory planning strong coding sql experience in python and redshif...
- **JD snippet:** we are looking for an experienced engineer who has participated in the entire software development life cycle and has knowledge of various architecture patterns and agile methodologies the ideal candi...

### Error Case 2: Actual `Potential Fit` -> Predicted `Good Fit`
- **Resume snippet:** summarysenior software engineer passionate about creating cutting edge products for enterprise level initiatives strong work ethic and dedicated to quality assurance adept at working with teams or ind...
- **JD snippet:** about the jobwe are seeking a senior full stack software engineer to build and scale business critical web products this is a unique opportunity to work alongside an experienced team that excels at bu...

### Error Case 3: Actual `No Fit` -> Predicted `Potential Fit`
- **Resume snippet:** summaryadaptable software engineer ready to support operations from conception through post release support skilled creator of efficient code and exciting user experiences eager to elevate ongoing dev...
- **JD snippet:** this internship is in person in omaha ne for the duration of the internship candidates will be expected to work approximately 20 hours per week during the school year milliman is an international cons...

### Error Case 4: Actual `No Fit` -> Predicted `Potential Fit`
- **Resume snippet:** professional profilehighly motivated sales associate with extensive customer service and sales experience outgoing sales professional with track record of driving increased sales improving buying expe...
- **JD snippet:** job role data analyst 1 open role location dallas tx candidate must be working at onsite duration long term note looking for candidates with strong sql and data warehousingetl experience telecom backg...

### Error Case 5: Actual `Potential Fit` -> Predicted `Good Fit`
- **Resume snippet:** summary hands on self motivated technology architect with over 10 years of experience deep programming acumen and the ability to rapidly design code implementdeep expertise and understand challenges a...
- **JD snippet:** company descriptionmtk technologies is a premier hr solutions and services organization providing quality skilled manpower to clients in various industries established in 2006 we are committed to beco...

### Key Baseline Weaknesses Identified:
1. **Bag-of-Words Limitations:** Standard TF-IDF treats words independently, failing to capture semantic synonyms.
2. **Context-Insensitive Matching:** High overlap on generic resume boilerplate inflates similarity.
3. **Class Imbalance in Boundary Cases:** Distinguishing between 'Potential Fit' and 'Good Fit' requires deeper semantic reasoning.

## 6. Sprint 2 Measurable Improvement Targets
Based on the baseline results, the following targets are established for Sprint 2:
- **Target Metric 1 (Macro F1):** Improve Macro F1 from **67.89%** to **>= 72.89%** (+5% absolute gain via embeddings/LightGBM/feature engineering).
- **Target Metric 2 (Good Fit Recall):** Improve Good Fit recall beyond **80.99%**.
- **Target Metric 3 (Inference Latency):** Keep model inference time **< 100ms** per CV-JD pair.
