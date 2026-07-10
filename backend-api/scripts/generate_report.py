import sys
sys.path.insert(0, ".")

import json
from pathlib import Path


def main():
    with open("reports/rag_evaluation_results.json") as f:
        rag = json.load(f)

    with open("reports/final_summary.json") as f:
        baseline = json.load(f)

    top = baseline["ranking_by_test_weighted_f1"][0]
    baseline_model = top["model"]
    baseline_f1 = top["test_f1"]

    rag_f1 = rag["queue_metrics"]["weighted_f1"]
    delta = round(rag_f1 - baseline_f1, 4)
    pct = round(delta / baseline_f1 * 100, 2)
    sign = "+" if delta >= 0 else ""

    report = f"""# RAG vs Baseline Report

## Setup

| Parameter | Value |
|---|---|
| Embedding model | all-MiniLM-L6-v2 |
| LLM | {rag['model']} |
| Top-K retrieval | {rag['top_k']} |
| Evaluation sample | {rag['sample_size']} tickets (stratified from test set) |

## Queue Classification

| Model | Weighted F1 |
|---|---|
| {baseline_model} — M2 baseline (full test set, n=4217) | {baseline_f1} |
| RAG majority vote — M3 (stratified sample, n={rag['sample_size']}) | {rag_f1} |

**Delta: {sign}{delta} ({sign}{pct}%)**

> The baseline was evaluated on the full 4,217-ticket test set.
> RAG classification uses a stratified {rag['sample_size']}-ticket sample.
> Direct F1 comparison is indicative, not exact.

## Answer Generation

| Metric | Value |
|---|---|
| Mean BLEU | {rag['answer_metrics']['mean_bleu']} |
| Mean ROUGE-L | {rag['answer_metrics']['mean_rouge_l']} |

Answer generation has no M2 equivalent — these metrics measure how closely
the LLM-generated response matches the ground-truth agent answer.
"""

    Path("reports").mkdir(exist_ok=True)
    with open("reports/rag_vs_baseline.md", "w") as f:
        f.write(report)

    print("Saved: reports/rag_vs_baseline.md")
    print(f"\nRAG F1      : {rag_f1}")
    print(f"Baseline F1 : {baseline_f1} ({baseline_model})")
    print(f"Delta       : {sign}{delta} ({sign}{pct}%)")


if __name__ == "__main__":
    main()