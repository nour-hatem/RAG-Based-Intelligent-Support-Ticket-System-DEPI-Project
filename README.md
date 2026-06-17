# Member 2 — NLP / ML Engineer (Milestone 2: Baseline, Embeddings & Retrieval)

Pipeline implementing: SentenceTransformer embeddings, three tuned TF-IDF
baseline classifiers (Logistic Regression, Random Forest, Linear SVM),
a cosine-similarity FAISS index, evaluation metrics, MLflow experiment
tracking (SQLite backend), and a final comparison report.

## Run order

```bash
pip install -r requirements.txt

python 01_generate_embeddings.py   # needs internet access to huggingface.co
python 02_baseline_model.py        # tunes & trains LogReg, RF, SVM on val; saves to models/
python 03_faiss_index.py           # builds IndexFlatIP (cosine similarity) over embeddings
python 04_evaluation.py            # test-set classification metrics + retrieval metrics
python 05_mlflow_tracking.py       # logs all 4 runs to sqlite:///mlflow.db
python 06_final_report.py          # writes reports/final_summary.{json,md}
```

Run `01_generate_embeddings.py` somewhere with HuggingFace Hub access
(Colab, local machine, Azure ML). It downloads `all-MiniLM-L6-v2` once
and caches it; every later step only reads the saved `.npy` files, so
they can run anywhere once embeddings exist — including network-restricted
sandboxes.

## Inputs (from Milestone 1)

```
data/processed/cleaned_corpus.csv
data/processed/train.csv   (19,679 rows)
data/processed/val.csv     (4,217 rows)
data/processed/test.csv    (4,217 rows)
```

## Outputs

| Path | Description |
|---|---|
| `embeddings/body_embeddings.npy` | Full-corpus SentenceTransformer embeddings (N × 384) |
| `embeddings/train_embeddings.npy` | Train split embeddings (19,679 × 384) |
| `embeddings/val_embeddings.npy` | Val split embeddings (4,217 × 384) |
| `embeddings/test_embeddings.npy` | Test split embeddings (4,217 × 384) |
| `models/tfidf_logreg_baseline.pkl` | TF-IDF + Logistic Regression (tuned on val) |
| `models/tfidf_rf_baseline.pkl` | TF-IDF + Random Forest (tuned on val, joblib-compressed) |
| `models/tfidf_svm_baseline.pkl` | TF-IDF + Linear SVM (tuned on val) |
| `models/test_predictions.csv` | Test-set predictions from all three models |
| `models/tuning_results.json` | Every validation grid candidate tried, for all 3 models |
| `plots/confusion_matrix_logreg.png` | Confusion matrix, test set |
| `plots/confusion_matrix_rf.png` | Confusion matrix, test set |
| `plots/confusion_matrix_svm.png` | Confusion matrix, test set |
| `faiss/faiss.index` | FAISS `IndexFlatIP` (cosine similarity) over train embeddings |
| `reports/evaluation_results.json` | Accuracy / Precision / Recall / F1 + retrieval stats (all 3 models) |
| `reports/final_summary.json` / `.md` | Ranked model comparison + recommendation |
| `mlflow.db` | MLflow SQLite backend store — 4 runs (LogReg, RF, SVM, FAISS retrieval) |

## Viewing MLflow results

```bash
mlflow ui --backend-store-uri sqlite:///mlflow.db
```

## Model selection methodology

All three baselines are tuned with a manual grid search **on the
validation set only** (the test set is touched exactly once, after each
model's winning configuration is locked in):

- **Logistic Regression** — grid over `C` and `class_weight`.
- **Random Forest** — grid over `n_estimators`, `min_samples_leaf`, `max_depth`.
- **Linear SVM (`LinearSVC`)** — grid over `C` and `class_weight`.

Each grid candidate is scored by weighted F1 on `val.csv`; the best
config per model family is refit and evaluated once on `test.csv`.
Every candidate tried is logged in `models/tuning_results.json` for
auditability.

## Results (test set, weighted F1, best config per model)

| Rank | Model | Accuracy | Precision | Recall | F1 (weighted) |
|---|---|---|---|---|---|
| 1st | **Linear SVM** | 0.732 | 0.742 | 0.732 | **0.731** |
| 2nd | Logistic Regression | 0.700 | 0.723 | 0.700 | 0.697 |
| 3rd | Random Forest | 0.682 | 0.714 | 0.682 | 0.684 |

**Recommended baseline: Linear SVM** (`tfidf_svm_baseline.pkl`, `C=1.0`,
`class_weight=None`) — highest test weighted F1 of the three, selected
purely on validation performance with no test-set leakage. See
`reports/final_summary.md` for the full breakdown, retrieval metrics,
and per-class detail.

## Retrieval (FAISS, IndexFlatIP / cosine similarity)

| Metric | Value |
|---|---|
| Retrieval@1 | 0.818 |
| Retrieval@3 | 0.872 |
| Retrieval@5 | 0.903 |
| Retrieval@10 | 0.942 |
| MRR@10 | 0.853 |
| Mean top-1 cosine similarity | 0.934 |

## Key implementation notes

- **Embeddings**: real `SentenceTransformer('all-MiniLM-L6-v2')` output,
  `normalize_embeddings=True` (unit L2 norm, verified at index-build time).
  Text column: `clean_body` (falls back to `lemmatized_body` if absent).
- **FAISS metric**: `IndexFlatIP`, not `IndexFlatL2`. For unit-normalized
  vectors, `||a-b||^2 = 2 - 2(a·b)`, so ranking by smallest L2 distance and
  by largest inner product produce identical neighbor orderings — but
  inner product on unit vectors **is** cosine similarity by definition,
  giving directly interpretable [0,1] scores instead of unitless distances.
  See the docstring in `03_faiss_index.py` for the full derivation.
- **LogReg convergence fix**: `max_iter` raised from 1000 → 4000, and the
  grid search uses `solver='lbfgs'` (multiclass-native, converges in
  60–250 iterations on this data — far inside the new budget) instead of
  `saga`, which needed thousands of iterations per candidate and made an
  8-way grid impractically slow without changing the result. Every run
  asserts `n_iter_ < max_iter` after fitting to verify convergence
  explicitly rather than just suppressing the warning.
- **Random Forest depth**: `max_depth=None` (unbounded) was tested and
  excluded from the grid — on this 50k-feature sparse TF-IDF matrix it
  produces extremely deep, slow-to-fit trees for no measurable F1 gain
  over depth 30–50. The chosen config (`max_depth=50`) is depth-capped
  for tractable train time with a compressed (joblib) ~13–17MB artifact.
- **MLflow backend**: `sqlite:///mlflow.db`, replacing the deprecated
  plain file store (`file:mlruns`). Params logged per run are read
  dynamically from `models/tuning_results.json`, so they can never drift
  out of sync with what was actually trained.

## requirements.txt

See `requirements.txt` for pinned versions (pandas, numpy, scikit-learn,
sentence-transformers, torch, faiss-cpu, mlflow, matplotlib, joblib).

## Legacy file

`02b_tuned_baseline.py` is an earlier experiment (subject+body feature
trick on Logistic Regression only) that is **not** part of the current
run order above — it's superseded by the tuned Linear SVM in
`02_baseline_model.py`, which now scores higher (F1=0.731 vs 0.730) using
a more principled three-model validation-based selection process. Kept
for reference; safe to delete.
