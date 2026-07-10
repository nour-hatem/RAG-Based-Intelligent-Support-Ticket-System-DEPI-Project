# Preprocessing Documentation - Milestone 1
**Project:** Intelligent Support Ticket Classification with RAG
**Dataset:** `Tobi-Bueck/customer-support-tickets` (HuggingFace Hub)
**Author:** Data Engineering - M1 Team
**Date:** June 2026
**Notebook:** `m1_data_pipeline.ipynb`

---

## 1. Overview

This document describes every decision made during data collection and preprocessing for Milestone 1. The goal is to produce a clean, embedded, and properly split corpus that Milestone 2 can consume directly without any re-processing.

The source dataset is a publicly available customer support ticket collection from HuggingFace Hub. It closely mirrors the schema (body text, assigned queue, priority, type, answer, tags) and scale (~61.8k rows) of a production support system.

---

## 2. Pipeline Overview

```
Raw dataset (HuggingFace)
        │
        ▼
Language validation → English filter
        │
        ▼
Data quality checks (nulls, duplicates, body-queue correlation)
        │
        ▼
Text cleaning (Unicode norm → URL/email strip → lowercase → strip non-alnum)
        │
        ▼
Extreme length filter (30–5000 chars on clean_body)
        │
        ▼
Lemmatization + domain stopword removal (spaCy en_core_web_sm)
        │
        ▼
Tokenization analysis (all-MiniLM-L6-v2 tokenizer, 5000-row sample)
        │
        ▼
Sentence embeddings (all-MiniLM-L6-v2, 384-dim, L2-normalized)
        │
        ▼
Stratified train / val / test split (70 / 15 / 15)
        │
        ▼
Export: cleaned_corpus.csv + split CSVs + .npy embedding files
```

---

## 3. Dataset

| Property | Value |
|---|---|
| Source | `Tobi-Bueck/customer-support-tickets` via HuggingFace `datasets` |
| Raw rows | ~61,800 |
| Languages | English, German |
| Key columns | `body`, `answer`, `queue`, `priority`, `type`, `language`, `tag_1`–`tag_8` |
| Column note | Column name changed between dataset versions (`issue_description` → `body`). Schema is validated programmatically at load time. |

**Why this dataset?**
No proprietary ticket database was available for this academic project. This HuggingFace dataset provides a realistic distribution of ticket categories, priorities, and free-text fields that closely match production support systems.

---

## 4. Step-by-Step Pipeline

### 4.1 Schema Validation at Load Time

Before any processing, the notebook confirms that all expected columns exist and prints shape + dtypes. This is a hard fail-fast check, if any expected column is missing, the notebook errors early rather than silently producing a malformed corpus.

---

### 4.2 Language Validation & English-Only Filtering

**Action:** Retained only rows where `language == "en"`, dropped all German (`"de"`) rows.

**Rationale:** The full downstream pipeline - spaCy `en_core_web_sm` for lemmatization and `all-MiniLM-L6-v2` for embeddings - is English-only. Passing German text through these models produces garbage tokens and corrupted embedding vectors without raising any error, silently degrading retrieval quality.

**Validation step:** The `language` column was validated on a 200-row sample using `langdetect`. The column proved reliable (≥ 95% accuracy), so the filter was applied directly.

| Threshold | Action |
|---|---|
| Accuracy ≥ 95% | Filter directly on `df["language"] == "en"` |
| Accuracy < 95% | Supplement with per-row `langdetect` detection |

**Impact:** German rows (~30% of the raw dataset) were dropped.

---

### 4.3 Data Quality Checks

Three checks were performed in sequence:

**Null counts:** Tag columns `tag_4` through `tag_8` contain nulls - this is expected. Core columns (`body`, `queue`, `answer`) had no nulls after filtering.

**Full-row duplicates:** Exact duplicate rows were detected and their count logged. These represent tickets submitted multiple times or export artifacts and were removed.

**Body-to-queue correlation:** Each unique `body` text was checked - does it always map to the same `queue` label?

```python
df.groupby("body")["queue"].nunique()
```

Result: over 99% of body texts map to exactly one queue, confirming `queue` is a clean and trustworthy classification target. This is the most important quality gate in M1 - if it had failed, the entire M2 classification task would have needed a different label strategy.

---

### 4.4 Text Cleaning

**Function:** `clean_text(text: str) -> str`

Applied to both `body` → `clean_body` and `answer` → `clean_answer`.

| Step | Operation | Rationale |
|---|---|---|
| Unicode NFKC normalization | `unicodedata.normalize("NFKC", text)` | Converts smart quotes, em-dashes, accented chars to canonical form - prevents tokenization fragmentation |
| URL removal | Regex `https?://\S+` and `www.\S+` → space | URLs expand into meaningless subword tokens |
| Email removal | Regex `\S+@\S+\.\S+` → space | Non-informative for classification; also a PII concern |
| Lowercase | `text.lower()` | Reduces vocabulary size and prevents case-based mismatches |
| Strip non-alphanumeric | `[^a-z0-9\s]` → space | Removes punctuation noise; **digits intentionally kept** |
| Collapse whitespace | `\s+` → single space + `.strip()` | Normalizes all whitespace artifacts |

**Why keep digits?** Error codes (`404`, `0x8004005`), version strings (`v3.2.1`), and ticket reference numbers carry queue-specific signal. Stripping digits removes meaningful features.

---

### 4.5 Extreme Length Filtering

After cleaning, rows with extreme body lengths were dropped:

- **Minimum:** `clean_body` length < 30 characters → dropped. A 2–3 word ticket has no signal for retrieval or classification.
- **Maximum:** `clean_body` length > 5,000 characters → dropped. Typically auto-generated system dumps or copy-pasted logs, not human-written tickets.

This filter improves embedding quality and removes outliers that would skew model training (~200–400 rows removed).

---

### 4.6 Lemmatization & Stopword Removal

| Setting | Value |
|---|---|
| Library | spaCy |
| Model | `en_core_web_sm` |
| Disabled components | `parser`, `ner` (speeds up by ~40%) |
| Batch size | 256 |
| Optimization | Applied to unique texts only, then mapped back via dictionary lookup |

**Optimization rationale:** Many support tickets share identical phrasing. Processing only unique texts and mapping back cuts runtime by 40–60%.

**Token filter:** Keep a token if (a) not a spaCy built-in stopword, (b) not in the domain stopword list, and (c) token length > 2 characters.

**Domain-specific stopwords:** Words like `support`, `please`, `team`, `customer`, `help`, `ticket`, `issue`, `request`, `problem`, `contact` appear at near-uniform frequency across all queues - zero discriminative signal. Added to a custom `DOMAIN_STOPS` set on top of spaCy's built-in list.

**Output column:** `lemmatized_body` - used for EDA keyword analysis and available as TF-IDF input for M2 classical baselines.

---

### 4.7 Tokenization Analysis

**Tokenizer:** `AutoTokenizer.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")`

Applied to a 5,000-row random sample with `add_special_tokens=True` to match the model's actual behavior.

**Why this matters:** Character count and word count are not the right proxies for transformer input length. The model truncates silently at 512 subword tokens - using the actual tokenizer reveals the true distribution and quantifies how much content is lost.

**Threshold rule:**

| Truncation rate | Action |
|---|---|
| > 10% of tickets exceed 512 tokens | Flag for M2 - consider chunked mean-pooling |
| ≤ 10% | Standard `encode(text, truncation=True, max_length=512)` is safe |

**Result:** < 5% of tickets exceed 512 tokens - standard truncation is acceptable.

---

### 4.8 Sentence Embeddings Generation

| Setting | Value |
|---|---|
| Model | `sentence-transformers/all-MiniLM-L6-v2` |
| Input column | `clean_body` (not `lemmatized_body`) |
| Batch size | 64 |
| Output dimension | 384 |
| Normalization | L2-normalized (`normalize_embeddings=True`) |
| Output format | NumPy float32 array |

**Why `clean_body` not `lemmatized_body`?** The sentence-transformer has its own internal subword tokenizer. Heavy lemmatization degrades its performance - the model performs better on lightly cleaned natural text.

**Why L2-normalize?** Azure Cognitive Search and FAISS (used in M3) compute similarity via dot product. When vectors are L2-normalized, dot product equals cosine similarity, which is more meaningful for semantic search than Euclidean distance.

**Sanity check:** The L2 norm of the first embedding vector is printed after generation. Expected value: `1.000000`.

**Output:** `data/processed/body_embeddings.npy` - float32 array, shape `(N, 384)`.

---

### 4.9 Embeddings Visualization (PCA)

A 2D PCA projection of 3,000 randomly sampled embeddings is generated and saved as `embeddings_pca.png`. This is a visual sanity check - if queue classes form rough clusters in the 2D projection, it confirms the embeddings capture queue-discriminative semantics and M2's vector search will be meaningful.

---

### 4.10 Stratified Train / Validation / Test Split

| Split | Proportion | Purpose |
|---|---|---|
| Train | 70% | Model training |
| Validation | 15% | Hyperparameter tuning, early stopping |
| Test | 15% | Final held-out evaluation - do not touch until final M2 report |

**Why stratification is mandatory:** The queue distribution is imbalanced. Without stratification, rare queues could be completely absent from validation or test sets, making per-class metrics unreliable.

**Embedding sync:** Embedding indices are extracted using the DataFrame index before resetting it, then split arrays are saved alongside their corresponding CSV files. M2 can load `train.csv` + `train_embeddings.npy` together without re-running any embedding step.

`random_state=42` for full reproducibility.

---

### 4.11 Export - Full Cleaned Corpus

**File:** `data/processed/cleaned_corpus.csv`

Column selection is done defensively:

```python
keep_cols = ["body", "answer", "type", "queue", "priority"]
for opt in ["subject", "version"]:
    if opt in df.columns:
        keep_cols.insert(0, opt)
```

Optional columns are only included if they exist in the loaded DataFrame, preventing `KeyError` on dataset versions that omit them.

---

## 5. Key Columns in `cleaned_corpus.csv`

| Column | Source | Description |
|---|---|---|
| `body` | Raw | Original ticket text |
| `answer` | Raw | Original agent response |
| `queue` | Raw | Classification label (target for M2) |
| `priority` | Raw | Ticket priority level |
| `type` | Raw | Ticket type |
| `tag_1` … `tag_8` | Raw | Multi-label tags (sparse) |
| `clean_body` | Derived | Cleaned body text |
| `clean_answer` | Derived | Cleaned answer text |
| `lemmatized_body` | Derived | Lemmatized + stopword-removed body |
| `body_length` | Derived | Character count of raw body |
| `answer_length` | Derived | Character count of raw answer |
| `clean_answer_length` | Derived | Character count of clean answer |

---

## 6. Output Files

| File | Description | Used In |
|---|---|---|
| `cleaned_corpus.csv` | Full cleaned corpus with all derived columns | M2 - model training reference |
| `train.csv` | 70% training split | M2 - model training |
| `val.csv` | 15% validation split | M2 - hyperparameter tuning |
| `test.csv` | 15% held-out test split | M2 - final evaluation |
| `body_embeddings.npy` | Full embedding matrix `(N, 384)` float32 | M2 - FAISS index construction |
| `train_embeddings.npy` | Train split embeddings | M2 - classifier training |
| `val_embeddings.npy` | Val split embeddings | M2 - evaluation |
| `test_embeddings.npy` | Test split embeddings | M2 - final evaluation |
| `queue_distribution.png` | Bar chart of queue class counts | EDA report |
| `priority_type_distribution.png` | Priority and type distributions | EDA report |
| `text_length_distribution.png` | Body and answer length histograms | EDA report |
| `tag_distribution.png` | Top 20 tags across all tickets | EDA report |
| `queue_tag_heatmap.png` | Cross-tabulation of queue vs primary tag | EDA report |
| `token_count_distribution.png` | Subword token count distribution with 512-limit line | EDA report |
| `embeddings_pca.png` | 2D PCA of ticket embeddings colored by queue | EDA report |

---

## 7. Design Decisions Summary

| Decision | Choice | Alternative Considered | Reason for Choice |
|---|---|---|---|
| Proxy dataset | HuggingFace `Tobi-Bueck/customer-support-tickets` | Real enterprise DB | Not available; HuggingFace dataset has comparable schema and scale |
| Language filter | English only | Multilingual pipeline | spaCy and all-MiniLM are English-optimized; multilingual adds complexity for no accuracy gain at this scale |
| Keep digits in cleaning | Yes | Strip all non-alpha | Error codes and version numbers carry queue-specific signal |
| Embedding input | `clean_body` | `lemmatized_body` | Sentence-transformer has its own subword tokenizer; heavy lemmatization degrades its performance |
| L2 normalization | Enabled | Raw vectors | Required for dot-product similarity in FAISS and Azure Cognitive Search |
| Split ratio | 70/15/15 | 80/10/10 | Larger validation and test sets give more reliable per-class F1 across 15+ queue classes |

---

## 8. Environment & Reproducing the Pipeline

```bash
# 1. Install dependencies
pip install -r requirements.txt
python -m spacy download en_core_web_sm

# 2. Run the notebook top-to-bottom
jupyter nbconvert --to notebook --execute m1_data_pipeline.ipynb \
    --output m1_data_pipeline_executed.ipynb

# 3. Verify outputs
ls -lh data/processed/
```

---

## 9. Notes for Milestone 2

- Load embeddings with `np.load("data/processed/train_embeddings.npy")`.
- Labels are in `train.csv["queue"]` - ensure row order is preserved (both files have matching indices).
- Class imbalance metrics are logged in the notebook; check before choosing a loss function.
- `test.csv` / `test_embeddings.npy` are held-out - do not use for any training or tuning decisions.
- `lemmatized_body` is available for TF-IDF baselines to compare against RAG.
- Answer quality analysis results in the notebook indicate whether BLEU is a reliable standalone metric.

---

*Document prepared as part of the M1 deliverable package. See `m1_data_pipeline.ipynb` for the full executable implementation.*
