"""
Member 2 — Step 2b: Improved Baseline (LEGACY — superseded, kept for reference)
==================================================================================
STATUS: superseded by 02_baseline_model.py's tuned Linear SVM, which now
scores higher on the test set (F1=0.731) using proper validation-based
selection across three model families (LogReg, RF, SVM) rather than the
ad-hoc subject+body feature trick explored here. This script is kept only
as a record of an earlier experiment and is NOT part of the current
pipeline run order (see README.md). Safe to delete if you want a lean repo.

Original idea (still valid, just not the winning approach anymore):
Same mandated stack (TF-IDF + LogisticRegression) but tuned. Lifted
weighted F1 from 0.688 -> 0.730 on the test set vs. the plain (untuned)
baseline that existed before this milestone's validation-tuning rework.
Compare reports/tuned_evaluation_results.json (this script) against
reports/final_summary.json (current pipeline) — Linear SVM at 0.731
now edges this out.

What changed and why it helped:
  1. Combine subject + body text (subject repeated 2x for extra weight).
     Subject lines carry strong category signal that's diluted in body
     text alone — this was the single biggest contributor to the gain.
  2. GridSearchCV over TF-IDF max_features / ngram_range and
     LogisticRegression C / class_weight, using val as a held-out
     PredefinedSplit fold (not k-fold on train) so the search reflects
     real validation performance.
  3. lbfgs solver (supports multiclass natively, much faster than saga
     at this scale and gives equivalent results).
  4. Best params found: C=10.0, class_weight=None, max_features=40000,
     ngram_range=(1,2). class_weight=None outperformed 'balanced' here
     because the val set's class distribution matches the deployment
     distribution — forcing balance hurt majority classes more than it
     helped minority ones.

Input  : data/processed/{train,val,test}.csv
Output : models/tfidf_logreg_tuned.pkl
         reports/tuned_evaluation_results.json
"""
import os
import json
import pickle
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.model_selection import GridSearchCV, PredefinedSplit
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, classification_report

BASE = "data/processed/"
MODELS = "models/"
REPORTS = "reports/"
os.makedirs(MODELS, exist_ok=True)
os.makedirs(REPORTS, exist_ok=True)

train = pd.read_csv(BASE + "train.csv")
val   = pd.read_csv(BASE + "val.csv")
test  = pd.read_csv(BASE + "test.csv")


def combined_text(df):
    subj = df["subject"].fillna("").astype(str)
    body = df["lemmatized_body"].fillna("").astype(str)
    return subj + " " + subj + " " + body  # subject weighted 2x via repetition


X_train, y_train = combined_text(train), train["queue"]
X_val,   y_val   = combined_text(val),   val["queue"]
X_test,  y_test  = combined_text(test),  test["queue"]

X_tv = pd.concat([X_train, X_val], ignore_index=True)
y_tv = pd.concat([y_train, y_val], ignore_index=True)
test_fold = [-1] * len(X_train) + [0] * len(X_val)   # -1 = always train, 0 = val fold
ps = PredefinedSplit(test_fold)

pipe = Pipeline([
    ("tfidf", TfidfVectorizer(sublinear_tf=True, min_df=2)),
    ("clf",   LogisticRegression(max_iter=1000, solver="lbfgs", random_state=42)),
])

param_grid = {
    "tfidf__max_features": [40000],
    "tfidf__ngram_range":  [(1, 2)],
    "clf__C":              [1.0, 5.0, 10.0],
    "clf__class_weight":   ["balanced", None],
}

print("Running GridSearchCV (6 candidates)...")
search = GridSearchCV(pipe, param_grid, cv=ps, scoring="f1_weighted", n_jobs=2, verbose=1)
search.fit(X_tv, y_tv)

print("\nBest params:", search.best_params_)
print("Best CV (val) weighted F1:", round(search.best_score_, 4))

best_model = search.best_estimator_
best_model.fit(X_tv, y_tv)   # refit on train+val with best params

y_pred = best_model.predict(X_test)
metrics = {
    "accuracy":  round(accuracy_score(y_test, y_pred), 4),
    "precision": round(precision_score(y_test, y_pred, average="weighted", zero_division=0), 4),
    "recall":    round(recall_score(y_test, y_pred, average="weighted"), 4),
    "f1":        round(f1_score(y_test, y_pred, average="weighted"), 4),
}
print("\nTuned model — test set metrics:")
for k, v in metrics.items():
    print(f"  {k:10s}: {v}")

report = classification_report(y_test, y_pred, output_dict=True, zero_division=0)

with open(MODELS + "tfidf_logreg_tuned.pkl", "wb") as f:
    pickle.dump(best_model, f)

with open(REPORTS + "tuned_evaluation_results.json", "w") as f:
    json.dump({
        "best_params": search.best_params_,
        "val_f1_during_search": round(search.best_score_, 4),
        "test_metrics": metrics,
        "per_class_report": report,
    }, f, indent=2, default=str)

print("\nSaved: models/tfidf_logreg_tuned.pkl, reports/tuned_evaluation_results.json")
