import json
import pandas as pd
from pathlib import Path
from sklearn.model_selection import train_test_split

from src.config import settings
from src.models.ticket import Ticket
from src.services.rag.rag_pipeline import RAGPipeline
from src.evaluation.metrics import queue_accuracy, queue_f1, mean_bleu, mean_rouge_l


class Evaluator:
    def __init__(self, pipeline: RAGPipeline):
        self.pipeline = pipeline
        self.test_df = pd.read_csv(settings.test_csv_path)

    def _sample(self) -> pd.DataFrame:
        n = min(settings.eval_sample_size, len(self.test_df))
        if n == len(self.test_df):
            return self.test_df.reset_index(drop=True)
        _, sample = train_test_split(
            self.test_df,
            test_size=n,
            stratify=self.test_df["queue"],
            random_state=42,
        )
        return sample.reset_index(drop=True)

    def run(self, output_path: str = "reports/rag_evaluation_results.json") -> dict:
        sample = self._sample()
        print(f"Evaluating on {len(sample)} tickets...")

        y_true_queues: list[str] = []
        y_pred_queues: list[str] = []
        true_answers:  list[str] = []
        pred_answers:  list[str] = []
        abstained: int = 0

        for i, row in sample.iterrows():
            ticket = Ticket(
                subject=row["subject"] if pd.notna(row.get("subject", None)) else None,
                body=str(row["body"]),
            )
            try:
                response = self.pipeline.run(ticket)

                if response.needs_human_review:
                    # Count toward abstention; still count queue guess if one exists
                    abstained += 1
                    if response.predicted_queue and response.predicted_queue != "Unknown":
                        y_true_queues.append(str(row["queue"]))
                        y_pred_queues.append(response.predicted_queue)
                    continue

                y_true_queues.append(str(row["queue"]))
                y_pred_queues.append(response.predicted_queue)
                true_answers.append(str(row["answer"]))
                pred_answers.append(response.generated_answer)
            except Exception as e:
                print(f"  [row {i}] skipped: {e}")
                continue

            done = len(y_true_queues)
            if done % 50 == 0:
                print(f"  {done}/{len(sample)} done")

        total_processed = len(y_true_queues) + abstained
        abstention_rate = abstained / total_processed if total_processed > 0 else 0.0

        results = {
            "sample_size": total_processed,
            "abstained": abstained,
            "abstention_rate": round(abstention_rate, 4),
            "top_k": settings.top_k,
            "model": settings.model_name,
            "confidence_threshold": settings.confidence_threshold,
            "queue_metrics": {
                "accuracy": queue_accuracy(y_true_queues, y_pred_queues),
                "weighted_f1": queue_f1(y_true_queues, y_pred_queues),
            },
            "answer_metrics": {
                "scored_answers": len(pred_answers),
                "mean_bleu": mean_bleu(true_answers, pred_answers),
                "mean_rouge_l": mean_rouge_l(true_answers, pred_answers),
            },
        }

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(results, f, indent=2)

        print(f"\nSaved: {output_path}")
        return results