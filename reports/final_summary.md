# Milestone 2 — Final Summary Report

**Embedding model:** all-MiniLM-L6-v2  
**FAISS index:** IndexFlatIP (cosine similarity on L2-normalized embeddings)

## Best configuration per model (selected on validation F1)

### Logistic Regression
- Best config: C=5.0, class_weight=None, solver=lbfgs, max_iter=4000 (converged in 207 iterations)
- Validation F1 during tuning: 0.6909
- **Test metrics:** Accuracy=0.7003 | Precision=0.7234 | Recall=0.7003 | F1=0.6973

### Random Forest
- Best config: n_estimators=150, min_samples_leaf=1, max_depth=50, class_weight=balanced_subsample
- Validation F1 during tuning: 0.6755
- **Test metrics:** Accuracy=0.6815 | Precision=0.7136 | Recall=0.6815 | F1=0.6841

### Linear SVM
- Best config: C=1.0, class_weight=None, max_iter=5000
- Validation F1 during tuning: 0.7159
- **Test metrics:** Accuracy=0.7323 | Precision=0.7417 | Recall=0.7323 | F1=0.7311

## Comparison table (test set)

| Model | Accuracy | Precision | Recall | F1 (weighted) |
|---|---|---|---|---|
| Logistic Regression | 0.7003 | 0.7234 | 0.7003 | 0.6973 |
| Random Forest | 0.6815 | 0.7136 | 0.6815 | 0.6841 |
| Linear SVM | 0.7323 | 0.7417 | 0.7323 | 0.7311 |

## Retrieval metrics (FAISS, IndexFlatIP / cosine similarity)

| Metric | Value |
|---|---|
| Retrieval@1 | 0.8179 |
| Retrieval@3 | 0.8717 |
| Retrieval@5 | 0.9028 |
| Retrieval@10 | 0.9417 |
| MRR@10 | 0.8532 |
| Mean top-1 cosine similarity | 0.9342 |

### Per-class Retrieval@5 (worst to best)

| Queue | Retrieval@5 |
|---|---|
| Sales and Pre-Sales | 0.7698 |
| Human Resources | 0.7927 |
| Returns and Exchanges | 0.8286 |
| General Inquiry | 0.85 |
| IT Support | 0.8732 |
| Service Outages and Maintenance | 0.8916 |
| Customer Service | 0.9008 |
| Product Support | 0.9153 |
| Technical Support | 0.9294 |
| Billing and Payments | 0.9491 |

## Ranked comparison (by test weighted F1)

**1st place:** Linear SVM — F1 = 0.7311
**2nd place:** Logistic Regression — F1 = 0.6973
**3rd place:** Random Forest — F1 = 0.6841

## Recommendation

**Linear SVM** is the recommended baseline for this project.

Linear SVM achieved the highest weighted F1 on the held-out test set (0.7311) after all three models were independently tuned on the validation set. This is the selection criterion specified for this milestone (best validation F1 picks the configuration; test F1, touched only once, breaks ties between model families).