import faiss
import numpy as np
import pandas as pd
from src.config import settings
from src.models.ticket import RetrievedTicket


class FAISSRetriever:
    def __init__(self):
        self.index = faiss.read_index(str(settings.faiss_index_path))
        self.corpus = pd.read_csv(settings.train_csv_path)

    def retrieve(self, query_embedding: np.ndarray, top_k: int = settings.top_k) -> list[RetrievedTicket]:
        scores, indices = self.index.search(query_embedding, top_k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:
                continue

            row = self.corpus.iloc[idx]
            results.append(RetrievedTicket(
                subject=row["subject"] if pd.notna(row["subject"]) else None,
                body=row["body"],
                answer=row["answer"],
                queue=row["queue"],
                score=float(max(0.0, min(score, 1.0))),
            ))

        return results