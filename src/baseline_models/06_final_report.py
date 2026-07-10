"""
Member 2 — Step 6: Final Summary Report (NEW)
================================================
Pulls together tuning results, test metrics, and retrieval metrics into
one JSON and one Markdown report, with a ranked comparison of the three
baseline models and a recommendation.

Input:
    models/tuning_results.json
    reports/evaluation_results.json

Output:
    reports/final_summary.json
    reports/final_summary.md
"""
import json

REPORTS = "reports/"
MODELS  = "models/"

with open(MODELS + "tuning_results.json") as f:
    tuning = json.load(f)
with open(REPORTS + "evaluation_results.json") as f:
    eval_results = json.load(f)

models_info = {
    "Logistic Regression": {
        "best_config": tuning["logistic_regression"]["best"],
        "test_metrics": eval_results["logistic_regression"]["test_metrics"],
    },
    "Random Forest": {
        "best_config": tuning["random_forest"]["best"],
        "test_metrics": eval_results["random_forest"]["test_metrics"],
    },
    "Linear SVM": {
        "best_config": tuning["linear_svm"]["best"],
        "test_metrics": eval_results["linear_svm"]["test_metrics"],
    },
}

# Rank by weighted F1 on the test set (the metric specified for model selection)
ranked = sorted(models_info.items(), key=lambda kv: kv[1]["test_metrics"]["f1"], reverse=True)
ranking = [
    {"rank": i + 1, "model": name, "test_f1": info["test_metrics"]["f1"]}
    for i, (name, info) in enumerate(ranked)
]
best_model_name = ranked[0][0]

retrieval = eval_results["faiss_retrieval"]

summary = {
    "embedding_model": eval_results["embedding_model"],
    "faiss_index_type": eval_results["faiss_index_type"],
    "models": models_info,
    "retrieval_metrics": {
        "Retrieval@K": retrieval["test"],
        "MRR@10": retrieval["mrr_at_10"],
        "mean_top1_cosine_similarity": retrieval["mean_top1_cosine_similarity"],
        "per_class_retrieval_at_5": retrieval["per_class_retrieval_at_5"],
    },
    "ranking_by_test_weighted_f1": ranking,
    "recommended_model": best_model_name,
    "recommendation_rationale": (
        f"{best_model_name} achieved the highest weighted F1 on the held-out "
        f"test set ({ranked[0][1]['test_metrics']['f1']}) after all three "
        f"models were independently tuned on the validation set. This is "
        f"the selection criterion specified for this milestone (best "
        f"validation F1 picks the configuration; test F1, touched only "
        f"once, breaks ties between model families)."
    ),
}

with open(REPORTS + "final_summary.json", "w") as f:
    json.dump(summary, f, indent=2)


def fmt_metrics(m):
    return f"Accuracy={m['accuracy']} | Precision={m['precision']} | Recall={m['recall']} | F1={m['f1']}"


def fmt_config(model_name, cfg):
    if model_name == "Logistic Regression":
        return f"C={cfg['C']}, class_weight={cfg['class_weight']}, solver=lbfgs, max_iter=4000 (converged in {cfg.get('n_iter','?')} iterations)"
    if model_name == "Random Forest":
        return f"n_estimators={cfg['n_estimators']}, min_samples_leaf={cfg['min_samples_leaf']}, max_depth={cfg['max_depth']}, class_weight=balanced_subsample"
    if model_name == "Linear SVM":
        return f"C={cfg['C']}, class_weight={cfg['class_weight']}, max_iter=5000"
    return str(cfg)


medal = {1: "1st place", 2: "2nd place", 3: "3rd place"}

md_lines = []
md_lines.append("# Milestone 2 — Final Summary Report\n")
md_lines.append(f"**Embedding model:** {summary['embedding_model']}  ")
md_lines.append(f"**FAISS index:** {summary['faiss_index_type']}\n")

md_lines.append("## Best configuration per model (selected on validation F1)\n")
for name, info in models_info.items():
    md_lines.append(f"### {name}")
    md_lines.append(f"- Best config: {fmt_config(name, info['best_config'])}")
    md_lines.append(f"- Validation F1 during tuning: {info['best_config']['val_f1']}")
    md_lines.append(f"- **Test metrics:** {fmt_metrics(info['test_metrics'])}\n")

md_lines.append("## Comparison table (test set)\n")
md_lines.append("| Model | Accuracy | Precision | Recall | F1 (weighted) |")
md_lines.append("|---|---|---|---|---|")
for name, info in models_info.items():
    m = info["test_metrics"]
    md_lines.append(f"| {name} | {m['accuracy']} | {m['precision']} | {m['recall']} | {m['f1']} |")
md_lines.append("")

md_lines.append("## Retrieval metrics (FAISS, IndexFlatIP / cosine similarity)\n")
md_lines.append("| Metric | Value |")
md_lines.append("|---|---|")
for k, v in summary["retrieval_metrics"]["Retrieval@K"].items():
    md_lines.append(f"| {k} | {v} |")
md_lines.append(f"| MRR@10 | {summary['retrieval_metrics']['MRR@10']} |")
md_lines.append(f"| Mean top-1 cosine similarity | {summary['retrieval_metrics']['mean_top1_cosine_similarity']} |")
md_lines.append("")

md_lines.append("### Per-class Retrieval@5 (worst to best)\n")
md_lines.append("| Queue | Retrieval@5 |")
md_lines.append("|---|---|")
for cls, v in sorted(summary["retrieval_metrics"]["per_class_retrieval_at_5"].items(), key=lambda x: x[1]):
    md_lines.append(f"| {cls} | {v} |")
md_lines.append("")

md_lines.append("## Ranked comparison (by test weighted F1)\n")
for r in ranking:
    md_lines.append(f"**{medal[r['rank']]}:** {r['model']} — F1 = {r['test_f1']}")
md_lines.append("")

md_lines.append("## Recommendation\n")
md_lines.append(f"**{summary['recommended_model']}** is the recommended baseline for this project.\n")
md_lines.append(summary["recommendation_rationale"])

with open(REPORTS + "final_summary.md", "w") as f:
    f.write("\n".join(md_lines))

print("Saved reports/final_summary.json and reports/final_summary.md")
print("\nRanking:")
for r in ranking:
    print(f"  {medal[r['rank']]}: {r['model']} (F1={r['test_f1']})")
print(f"\nRecommended model: {best_model_name}")
