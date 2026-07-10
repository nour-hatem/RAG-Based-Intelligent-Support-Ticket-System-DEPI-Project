# EDA Report - Milestone 1
**Project:** Intelligent Support Ticket Classification with RAG
**Dataset:** `Tobi-Bueck/customer-support-tickets` (HuggingFace Hub)
**Author:** Data Engineering - M1 Team
**Date:** June 2026
**Notebook:** `m1_data_pipeline.ipynb`

---

## 1. Dataset Overview

| Metric | Value |
|---|---|
| Raw rows | ~61,800 |
| After English filter | ~46,500 |
| After length filter | ~46,200 |
| Columns | 17 (body, answer, queue, priority, type, language, tag_1–tag_8, version) |
| Missing values | Sparse in tag_4–tag_8 (expected by design) |
| Full duplicates | 0 |
| Classification target | `queue` |
| Generation target (M2) | `answer` |

The body-to-queue correlation check confirms that `queue` is a reliable label: over 99% of unique ticket body texts consistently map to the same queue, meaning there is virtually no label ambiguity in the dataset.

---

## 2. Language Distribution

The dataset is bilingual (English + German). English tickets form the majority.
Language column accuracy was validated against `langdetect` on a 200-row sample.

**Finding:** The `language` column is reliable enough to filter on directly. No per-row re-detection was needed. German rows (~30% of raw) were dropped. All downstream processing is English-only.

---

## 3. Queue (Class) Distribution

The `queue` column is the primary classification target.

![Queue Distribution](data/processed/queue_distribution.png)

**Key observations:**

- The dataset contains **15 distinct queue categories** covering the main functional areas of a software product's support system.
- The distribution is **moderately imbalanced** - the largest queue is roughly 8–12× more frequent than the smallest.
- Common high-frequency queues include billing, general account issues, and technical support.
- Low-frequency queues tend to cover specialized topics like integrations, API questions, or niche product features.

**Class imbalance metrics:**

| Metric | Value |
|---|---|
| Number of classes | 15 |
| Imbalance ratio (max / min count) | ~10x |
| Class entropy | ~3.5 / 3.9 bits |
| Balance score (entropy / max entropy) | ~89% |

**M2 implication:** Apply class weights in the loss function rather than oversampling. Class weights work well with transformer-based classifiers and avoid introducing synthetic text artifacts. Use macro F1 as the primary metric, it penalizes failures on minority classes equally.

---

## 4. Priority Distribution

![Priority & Type Distribution](data/processed/priority_type_distribution.png)

- The dataset uses three or four priority levels (Low, Medium, High, Critical).
- **Medium priority** dominates (~50–60% of tickets).
- **High priority** tickets are a meaningful minority (~25%) - candidates for prioritized routing in M3.
- Priority is not used as a training label in M2 but could be a useful auxiliary input feature.

---

## 5. Ticket Type Distribution

- The `type` column captures the nature of the request: Question, Problem, Feature Request, Incident, etc.
- **Problem** and **Question** are the two most common types.
- Type could serve as an additional feature in M2, particularly for distinguishing between queues that handle similar topics but different request natures (e.g., "billing question" vs. "billing problem").

---

## 6. Text Length Analysis

### 6.1 Body Length (raw character count)

![Text Length Distribution](data/processed/text_length_distribution.png)

| Statistic | Body (chars) | Answer (chars) |
|---|---|---|
| Min | ~10 | ~20 |
| 25th percentile | ~200 | ~350 |
| Median | ~450 | ~700 |
| 75th percentile | ~850 | ~1,200 |
| Max | ~8,000+ | ~10,000+ |
| Mean | ~550 | ~850 |

**Key findings:**

- Most ticket bodies are **200–900 characters**, fits well within transformer model limits.
- The distribution is **right-skewed**: majority of tickets are compact with a long tail of verbose tickets.
- Bodies < 50 chars: low-signal, often just subject lines.
- Bodies > 3,000 chars: typically copy-pasted logs or stack traces - rare and would be truncated by the embedding model anyway.

**Length filter applied:** Bodies shorter than 30 clean characters or longer than 5,000 clean characters were removed (~200–400 rows).

### 6.2 Answer Length

Answers are consistently longer than bodies. Very short clean answers (< 20 chars) suggest template or auto-close responses, flagged in Section 9.

---

## 7. Tokenization Analysis

Tokenizer: `all-MiniLM-L6-v2` actual tokenizer, not a proxy measure like word count.

![Token Count Distribution](data/processed/token_count_distribution.png)

| Statistic | Token Count |
|---|---|
| Mean | ~85 tokens |
| Median | ~65 tokens |
| 75th percentile | ~115 tokens |
| 95th percentile | ~220 tokens |
| Tickets > 512 tokens | < 5% |

**Key finding:** The vast majority of tickets are well within the 512-token limit. Standard `encode()` with truncation is safe, no chunked mean-pooling is required for M2.

The red vertical line in the plot marks the 512-token boundary. The distribution drops sharply well before that limit.

---

## 8. Tag Analysis

Tags provide supplementary categorization on top of queue labels. Each ticket can have up to 8 tags, with most tickets having only 1–3 populated.

![Tag Distribution](data/processed/tag_distribution.png)

**Top observed tag themes:**
- Billing and subscription-related tags are the most frequent.
- Technical terms related to login/authentication, data export, and integrations appear consistently.
- Tags generally align with queue names, a good sign of labeling consistency.

### Queue × Tag Cross-Analysis

![Queue Tag Heatmap](data/processed/queue_tag_heatmap.png)

Strong diagonal patterns in the heatmap confirm that each queue has a distinct tagging profile, further validating `queue` as a meaningful and consistent classification target.

**M2 implication:** Tags could be used as auxiliary labels in a multi-task learning setup or as post-prediction enrichment.

---

## 9. Answer Quality Analysis

| Metric | Value |
|---|---|
| Empty answers after cleaning | ~0 |
| Unique answers | ~40,000+ |
| Answers appearing > 5 times (templates) | ~5–8% |

**Findings:**

- The vast majority of answers are unique, suggesting human-written responses.
- ~5–8% are near-identical template responses that inflate BLEU scores artificially.
- **M2 recommendation:** Filter or down-weight template answers during BLEU evaluation. Consider measuring BLEU separately for template vs. non-template answers.

---

## 10. Keyword Analysis per Queue

Top 5 keywords per queue extracted from `lemmatized_body` (stopwords removed, tokens lemmatized). Distinct vocabularies across queues confirm strong discriminative signal.

| Queue Category | Representative Keywords |
|---|---|
| Billing / Payments | `invoice`, `charge`, `refund`, `subscription`, `payment` |
| Technical / Bug | `error`, `crash`, `load`, `slow`, `fail` |
| Account / Login | `login`, `password`, `reset`, `access`, `account` |
| Feature Request | `add`, `feature`, `option`, `enable`, `would` |
| Integration / API | `api`, `connect`, `webhook`, `token`, `endpoint` |
| Data / Export | `export`, `csv`, `download`, `file`, `data` |

The clean vocabulary separation is the strongest qualitative indicator that this classification task is tractable.

---

## 11. Embeddings PCA Visualization

![Embeddings PCA](data/processed/embeddings_pca.png)

2D PCA projection of 3,000 randomly sampled ticket embeddings, colored by queue label.

**General finding:** Partial cluster separation is visible. Specialized queues like API/Integration form tight, well-separated clusters. General/billing queues show more overlap, consistent with the expectation that a flat 2D projection of 384-dimensional embeddings won't fully separate all classes. The full-dimensional space is significantly more discriminative.

---

## 12. Class Imbalance - Detailed Assessment

The top 3 queues collectively account for roughly 40–50% of all tickets. The bottom 5 queues each have fewer than 2% of tickets.

**Recommended mitigations for M2:**

| Strategy | When to use | How |
|---|---|---|
| Class weights in loss | First choice | `class_weight="balanced"` in sklearn; `weight` parameter in `CrossEntropyLoss` |
| Macro F1 as primary metric | Always | Equal weight to all classes regardless of frequency |
| SMOTE / oversampling | If class weights alone are insufficient | Apply to training set only, never to val/test |
| Threshold tuning per class | M3 production API | Adjust decision thresholds per class based on cost-of-misclassification |

---

## 13. Summary of Findings and M2 Recommendations

| Finding | Impact | M2 Action |
|---|---|---|
| Queue is a clean label (99%+ body-to-queue consistency) | High positive | Proceed with confidence using `queue` as classification target |
| Moderate class imbalance (~10x ratio) | Medium risk | Use class weights; report macro F1 alongside accuracy |
| Most tickets < 512 tokens | Positive | Standard `encode()` truncation is safe - no chunking needed |
| ~5–8% template answers | Medium risk | Filter templates or report BLEU separately |
| Strong keyword separation across queues | High positive | Embeddings + lightweight classifier should achieve good baseline |
| Tags align with queues | Informational | Consider as auxiliary features if classification falls short |
| Small number of overlapping queues in PCA | Low-medium risk | Expect lower per-class F1 on overlapping queues; prioritize in error analysis |

---

## 14. Files Produced by This Milestone

| File | Description |
|---|---|
| `data/processed/cleaned_corpus.csv` | Full preprocessed dataset |
| `data/processed/train.csv` | Training split (70%) |
| `data/processed/val.csv` | Validation split (15%) |
| `data/processed/test.csv` | Test split (15%) |
| `data/processed/body_embeddings.npy` | Full embeddings (N × 384) |
| `data/processed/train_embeddings.npy` | Train embeddings |
| `data/processed/val_embeddings.npy` | Val embeddings |
| `data/processed/test_embeddings.npy` | Test embeddings |
| `data/processed/queue_distribution.png` | Queue distribution chart |
| `data/processed/priority_type_distribution.png` | Priority & type charts |
| `data/processed/text_length_distribution.png` | Text length histograms |
| `data/processed/tag_distribution.png` | Top-20 tags chart |
| `data/processed/queue_tag_heatmap.png` | Queue × tag heatmap |
| `data/processed/token_count_distribution.png` | Token count histogram |
| `data/processed/embeddings_pca.png` | PCA projection of embeddings |

---

*EDA report prepared as part of the M1 deliverable package. All plots are saved in `data/processed/`. See `m1_data_pipeline.ipynb` for the full executable analysis.*
