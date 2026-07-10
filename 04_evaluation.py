"""
Member 2 — Step 4: Evaluation (MANDATORY + extended)
=======================================================
Computes Accuracy, Precision, Recall, F1 for all THREE baseline
classifiers (Logistic Regression, Random Forest, Linear SVM) on the
test set, plus FAISS retrieval evaluation using the cosine-similarity
IndexFlatIP index built in step 3.

CHANGES IN THIS VERSION
------------------------
1. Added Linear SVM (`pred_svm`) alongside LogReg and RF — same metric
   set, same classification_report detail.
2. Retrieval evaluation updated for the IndexFlatIP (cosine similarity)
   index: index.search now returns similarity scores (higher = better)
   instead of L2 distances (lower = better), so the same Retrieval@K
   logic produces the SAME hit/miss outcomes as before (ranking is
   unchanged, see 03_faiss_index.py docstring for the proof) but the
   raw scores reported alongside are now directly interpretable as
   cosine similarity in [0, 1].
3. Added extra retrieval statistics beyond Retrieval@K:
     - Mean Reciprocal Rank (MRR): rewards getting the FIRST correct
       neighbor ranked higher, not just whether one exists in top-K.
     - Mean top-1 cosine similarity: a quality signal independent of
       label match — useful for spotting queries with no good match
       in the corpus at all (low similarity even if the label happens
       to match by chance).
     - Per-class Retrieval@5: surfaces which queues retrieve poorly
       (useful for prioritizing where the RAG pipeline in Member 3's
       work might need a fallback or reranking strategy).

Input:
    data/processed/{train,test}.csv
    models/test_predictions.csv
    embeddings/test_embeddings.npy
    faiss/faiss.index   (IndexFlatIP, cosine similarity)

Output:
    reports/evaluation_results.json
"""
import os
import json
import numpy as np
import pandas as pd
import faiss
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, classification_report

BASE   = "data/processed/"
MODELS = "models/"
EMB    = "embeddings/"
FAISSD = "faiss/"
OUT    = "reports/"
os.makedirs(OUT, exist_ok=True)

test  = pd.read_csv(BASE + "test.csv")
preds = pd.read_csv(MODELS + "test_predictions.csv")
y_true = test["queue"]


def clf_metrics(y_true, y_pred, name):
    m = {
        "accuracy":  round(accuracy_score(y_true, y_pred), 4),
        "precision": round(precision_score(y_true, y_pred, average="weighted", zero_division=0), 4),
        "recall":    round(recall_score(y_true, y_pred, average="weighted"), 4),
        "f1":        round(f1_score(y_true, y_pred, average="weighted"), 4),
    }
    print(f"\n{name}:")
    for k, v in m.items():
        print(f"  {k:10s}: {v}")
    return m


lr_metrics  = clf_metrics(y_true, preds["pred_logreg"], "TF-IDF + Logistic Regression (test set)")
rf_metrics  = clf_metrics(y_true, preds["pred_rf"],     "TF-IDF + Random Forest (test set)")
svm_metrics = clf_metrics(y_true, preds["pred_svm"],    "TF-IDF + Linear SVM (test set)")

lr_report  = classification_report(y_true, preds["pred_logreg"], output_dict=True, zero_division=0)
rf_report  = classification_report(y_true, preds["pred_rf"],     output_dict=True, zero_division=0)
svm_report = classification_report(y_true, preds["pred_svm"],    output_dict=True, zero_division=0)

# ═════════════════════════════════════════════════════════════════════════
# FAISS retrieval evaluation — IndexFlatIP / cosine similarity
# ═════════════════════════════════════════════════════════════════════════
train = pd.read_csv(BASE + "train.csv")
train_labels = train["queue"].values
test_labels  = y_true.values

index = faiss.read_index(FAISSD + "faiss.index")
test_emb = np.load(EMB + "test_embeddings.npy").astype("float32")
assert test_emb.shape[1] == 384, "expected real 384-dim SentenceTransformer embeddings"


def retrieval_at_k(query_embs, query_labels, k_vals=(1, 3, 5, 10)):
    """Retrieval@K: fraction of queries whose true label appears among the
    label-set of the top-K retrieved neighbors. Higher score == more similar
    on IndexFlatIP, so search() already returns neighbors in the right order
    without any sign flip needed (unlike IndexFlatL2, where lower==better)."""
    results = {}
    for k in k_vals:
        _, I = index.search(query_embs, k)
        hits = sum(
            1 for i, row in enumerate(I)
            if query_labels[i] in [train_labels[j] for j in row if j != -1]
        )
        results[f"Retrieval@{k}"] = round(hits / len(query_labels), 4)
    return results


def mean_reciprocal_rank(query_embs, query_labels, k=10):
    """MRR: for each query, find the rank of the FIRST neighbor (within top-k)
    whose label matches the query's true label, take 1/rank, average over
    all queries (0 if no match found in top-k)."""
    _, I = index.search(query_embs, k)
    reciprocal_ranks = []
    for i, row in enumerate(I):
        rr = 0.0
        for rank, j in enumerate(row, start=1):
            if j != -1 and train_labels[j] == query_labels[i]:
                rr = 1.0 / rank
                break
        reciprocal_ranks.append(rr)
    return round(float(np.mean(reciprocal_ranks)), 4)


def mean_top1_similarity(query_embs):
    """Average cosine similarity of the single nearest neighbor, regardless
    of label match — a corpus-coverage signal: low values mean the test
    query has nothing genuinely similar in the training corpus at all."""
    D, _ = index.search(query_embs, 1)
    return round(float(np.mean(D[:, 0])), 4)


def per_class_retrieval_at_k(query_embs, query_labels, k=5):
    """Retrieval@k broken out by true queue label."""
    _, I = index.search(query_embs, k)
    per_class = {}
    for cls in sorted(set(query_labels)):
        idxs = [i for i, lbl in enumerate(query_labels) if lbl == cls]
        if not idxs:
            continue
        hits = sum(
            1 for i in idxs
            if query_labels[i] in [train_labels[j] for j in I[i] if j != -1]
        )
        per_class[cls] = round(hits / len(idxs), 4)
    return per_class


retrieval_results       = retrieval_at_k(test_emb, test_labels)
mrr                      = mean_reciprocal_rank(test_emb, test_labels, k=10)
mean_top1_sim            = mean_top1_similarity(test_emb)
per_class_retrieval_at_5 = per_class_retrieval_at_k(test_emb, test_labels, k=5)

print("\nFAISS Retrieval@K (test set, cosine similarity / IndexFlatIP, real all-MiniLM-L6-v2 embeddings):")
for k, v in retrieval_results.items():
    print(f"  {k}: {v}")
print(f"  Mean Reciprocal Rank (MRR@10): {mrr}")
print(f"  Mean top-1 cosine similarity:  {mean_top1_sim}")
print("\nPer-class Retrieval@5:")
for cls, v in sorted(per_class_retrieval_at_5.items(), key=lambda x: x[1]):
    print(f"  {cls:35s}: {v}")

# ═════════════════════════════════════════════════════════════════════════
# Save everything
# ═════════════════════════════════════════════════════════════════════════
eval_results = {
    "embedding_model": "all-MiniLM-L6-v2",
    "faiss_index_type": "IndexFlatIP (cosine similarity on L2-normalized embeddings)",
    "logistic_regression": {"test_metrics": lr_metrics, "per_class_report": lr_report},
    "random_forest":       {"test_metrics": rf_metrics, "per_class_report": rf_report},
    "linear_svm":          {"test_metrics": svm_metrics, "per_class_report": svm_report},
    "faiss_retrieval": {
        "test": retrieval_results,
        "mrr_at_10": mrr,
        "mean_top1_cosine_similarity": mean_top1_sim,
        "per_class_retrieval_at_5": per_class_retrieval_at_5,
    },
}
with open(OUT + "evaluation_results.json", "w") as f:
    json.dump(eval_results, f, indent=2)

print("\nSaved evaluation report to", OUT + "evaluation_results.json")
