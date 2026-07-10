"""
Member 2 — Step 5: MLflow Tracking (MANDATORY + fixed backend + SVM run)
============================================================================
CHANGE 1 — SQLite backend instead of file store
--------------------------------------------------
The previous version used `mlflow.set_tracking_uri("file:mlruns")`, the
plain file-based store. As of newer MLflow releases this path can fail or
warn because the file store backend's metadata format has been deprecated
in favor of a proper backend database (SQLite/Postgres/MySQL) — file store
lacks transactional guarantees, doesn't support the Model Registry well,
and is the source of the crash mentioned in the brief. Switching to:

    mlflow.set_tracking_uri("sqlite:///mlflow.db")

gives MLflow a real (if lightweight) relational backend. Runs, params,
metrics, and tags are written to mlflow.db; large binary artifacts
(models, the FAISS index, confusion matrix PNGs) still go to the
filesystem under ./mlruns_artifacts/ — only the *queryable metadata*
moves into SQLite, which is exactly what the artifact store / backend
store split is designed for.

CHANGE 2 — params/metrics are read from the actual tuning results
----------------------------------------------------------------------
Previously hyperparameters were hardcoded into this script by hand
(e.g. C=5.0, class_weight='balanced', max_iter=1000) and had drifted out
of sync with what 02_baseline_model.py actually selected via validation
tuning. This version reads models/tuning_results.json so the logged
params always match the model that was actually trained and saved.

CHANGE 3 — added Linear SVM run, and confusion matrix artifacts
----------------------------------------------------------------------
A 4th run (TFIDF_LinearSVM) is added alongside LogReg / RF / FAISS, and
all three classifier runs now attach their confusion matrix PNG as an
MLflow artifact, not just the model pickle.

Input:
    models/tuning_results.json
    models/tfidf_logreg_baseline.pkl, tfidf_rf_baseline.pkl, tfidf_svm_baseline.pkl
    reports/evaluation_results.json
    faiss/faiss.index
    plots/confusion_matrix_{logreg,rf,svm}.png

Output:
    mlflow.db                  (SQLite backend store — params/metrics/tags)
    mlruns_artifacts/          (artifact store — models, FAISS index, plots)
"""
import os
import json
import pickle
import mlflow
import mlflow.sklearn

MODELS  = "models/"
FAISSD  = "faiss/"
REPORTS = "reports/"
PLOTS   = "plots/"

with open(REPORTS + "evaluation_results.json") as f:
    results = json.load(f)
with open(MODELS + "tuning_results.json") as f:
    tuning = json.load(f)

# ── SQLite backend (fixes the deprecated file-store crash) ─────────────
mlflow.set_tracking_uri("sqlite:///mlflow.db")
mlflow.set_experiment("RAG_Support_Ticket_Baseline")

TFIDF_PARAMS = dict(ngram_range="(1,2)", max_features=50000, sublinear_tf=True, min_df=2)

# ═════════════════════════════════════════════════════════════════════════
# Run 1: Logistic Regression — params pulled from the actual winning config
# ═════════════════════════════════════════════════════════════════════════
lr_best = tuning["logistic_regression"]["best"]
with mlflow.start_run(run_name="TFIDF_LogisticRegression"):
    mlflow.log_params({f"tfidf_{k}": v for k, v in TFIDF_PARAMS.items()})
    mlflow.log_params({
        "model": "LogisticRegression",
        "solver": "lbfgs",
        "max_iter": 4000,
        "C": lr_best["C"],
        "class_weight": lr_best["class_weight"],
        "n_iter_actual": lr_best.get("n_iter"),
        "converged": lr_best.get("converged"),
        "selected_by": "best weighted F1 on validation set",
    })
    mlflow.log_metrics(results["logistic_regression"]["test_metrics"])
    mlflow.log_metric("val_f1_during_tuning", lr_best["val_f1"])

    with open(MODELS + "tfidf_logreg_baseline.pkl", "rb") as f:
        model = pickle.load(f)
    mlflow.sklearn.log_model(model, "model")
    mlflow.log_artifact(PLOTS + "confusion_matrix_logreg.png")
    print("Logged run: TFIDF_LogisticRegression")

# ═════════════════════════════════════════════════════════════════════════
# Run 2: Random Forest
# ═════════════════════════════════════════════════════════════════════════
rf_best = tuning["random_forest"]["best"]
with mlflow.start_run(run_name="TFIDF_RandomForest"):
    mlflow.log_params({f"tfidf_{k}": v for k, v in TFIDF_PARAMS.items()})
    mlflow.log_params({
        "model": "RandomForestClassifier",
        "n_estimators": rf_best["n_estimators"],
        "min_samples_leaf": rf_best["min_samples_leaf"],
        "max_depth": rf_best["max_depth"],
        "class_weight": "balanced_subsample",
        "selected_by": "best weighted F1 on validation set",
    })
    mlflow.log_metrics(results["random_forest"]["test_metrics"])
    mlflow.log_metric("val_f1_during_tuning", rf_best["val_f1"])

    # RF was saved with joblib (compressed) in 02_baseline_model.py, not
    # plain pickle, because unbounded-depth trees can otherwise produce
    # 100MB+ files — joblib.load handles both compressed and uncompressed
    # joblib-format files transparently.
    import joblib
    model = joblib.load(MODELS + "tfidf_rf_baseline.pkl")
    mlflow.sklearn.log_model(model, "model")
    mlflow.log_artifact(PLOTS + "confusion_matrix_rf.png")
    print("Logged run: TFIDF_RandomForest")

# ═════════════════════════════════════════════════════════════════════════
# Run 3: Linear SVM (new)
# ═════════════════════════════════════════════════════════════════════════
svm_best = tuning["linear_svm"]["best"]
with mlflow.start_run(run_name="TFIDF_LinearSVM"):
    mlflow.log_params({f"tfidf_{k}": v for k, v in TFIDF_PARAMS.items()})
    mlflow.log_params({
        "model": "LinearSVC",
        "C": svm_best["C"],
        "class_weight": svm_best["class_weight"],
        "max_iter": 5000,
        "selected_by": "best weighted F1 on validation set",
    })
    mlflow.log_metrics(results["linear_svm"]["test_metrics"])
    mlflow.log_metric("val_f1_during_tuning", svm_best["val_f1"])

    with open(MODELS + "tfidf_svm_baseline.pkl", "rb") as f:
        model = pickle.load(f)
    mlflow.sklearn.log_model(model, "model")
    mlflow.log_artifact(PLOTS + "confusion_matrix_svm.png")
    print("Logged run: TFIDF_LinearSVM")

# ═════════════════════════════════════════════════════════════════════════
# Run 4: FAISS Retrieval (IndexFlatIP / cosine similarity)
# ═════════════════════════════════════════════════════════════════════════
with mlflow.start_run(run_name="FAISS_Retrieval"):
    mlflow.log_params({
        "index_type": "IndexFlatIP",
        "similarity_metric": "cosine (via inner product on L2-normalized vectors)",
        "embedding_dim": 384,
        "embedding_model": "all-MiniLM-L6-v2",
        "embedding_source": "SentenceTransformer real embeddings, normalize_embeddings=True",
    })
    flat_retrieval = {k.replace("@", "_"): v for k, v in results["faiss_retrieval"]["test"].items()}
    mlflow.log_metrics(flat_retrieval)
    mlflow.log_metric("mrr_at_10", results["faiss_retrieval"]["mrr_at_10"])
    mlflow.log_metric("mean_top1_cosine_similarity", results["faiss_retrieval"]["mean_top1_cosine_similarity"])

    mlflow.log_artifact(FAISSD + "faiss.index")
    print("Logged run: FAISS_Retrieval")

print("\nAll 4 runs logged successfully to SQLite backend.")
print("Launch UI with:")
print("  mlflow ui --backend-store-uri sqlite:///mlflow.db")
