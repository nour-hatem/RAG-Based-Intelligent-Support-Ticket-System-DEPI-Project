import numpy as np
from sklearn.metrics import accuracy_score, f1_score
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
from rouge_score import rouge_scorer as rs


def queue_accuracy(y_true: list[str], y_pred: list[str]) -> float:
    return round(float(accuracy_score(y_true, y_pred)), 4)


def queue_f1(y_true: list[str], y_pred: list[str]) -> float:
    return round(float(f1_score(y_true, y_pred, average="weighted", zero_division=0)), 4)


def bleu_score(reference: str, hypothesis: str) -> float:
    ref_tokens = reference.lower().split()
    hyp_tokens = hypothesis.lower().split()
    smoothie = SmoothingFunction().method1
    return round(float(sentence_bleu([ref_tokens], hyp_tokens, smoothing_function=smoothie)), 4)


def rouge_l_score(reference: str, hypothesis: str) -> float:
    scorer = rs.RougeScorer(["rougeL"], use_stemmer=True)
    result = scorer.score(reference, hypothesis)
    return round(float(result["rougeL"].fmeasure), 4)


def mean_bleu(references: list[str], hypotheses: list[str]) -> float:
    return round(float(np.mean([bleu_score(r, h) for r, h in zip(references, hypotheses)])), 4)


def mean_rouge_l(references: list[str], hypotheses: list[str]) -> float:
    return round(float(np.mean([rouge_l_score(r, h) for r, h in zip(references, hypotheses)])), 4)