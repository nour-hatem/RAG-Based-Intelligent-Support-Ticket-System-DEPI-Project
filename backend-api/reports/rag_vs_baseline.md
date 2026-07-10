# RAG vs Baseline Report

## Setup

| Parameter | Value |
|---|---|
| Embedding model | all-MiniLM-L6-v2 |
| LLM | llama-3.1-8b-instant |
| Top-K retrieval | 5 |
| Evaluation sample | 250 tickets (stratified from test set) |

## Queue Classification

| Model | Weighted F1 |
|---|---|
| Linear SVM — M2 baseline (full test set, n=4217) | 0.7311 |
| RAG majority vote — M3 (stratified sample, n=250) | 0.7223 |

**Delta: -0.0088 (-1.2%)**

> The baseline was evaluated on the full 4,217-ticket test set.
> RAG classification uses a stratified 250-ticket sample.
> Direct F1 comparison is indicative, not exact.

## Answer Generation

| Metric | Value |
|---|---|
| Mean BLEU | 0.4141 |
| Mean ROUGE-L | 0.5922 |

Answer generation has no M2 equivalent — these metrics measure how closely
the LLM-generated response matches the ground-truth agent answer.
