from sentence_transformers import CrossEncoder
from src.config import settings
from src.models.ticket import RetrievedTicket


class CrossEncoderReranker:
    """Re-ranks FAISS top-K results using a cross-encoder model.

    Cross-encoder scores are NOT bounded [0, 1] - they must never be used
    for abstention threshold comparisons. Re-ranking is purely for ordering
    the retrieved tickets before prompt construction.
    """

    def __init__(self):
        self.model = CrossEncoder(settings.rerank_model_name)

    def rerank(self, query: str, tickets: list[RetrievedTicket]) -> list[RetrievedTicket]:
        """Return tickets re-ordered by cross-encoder relevance score, truncated to RERANK_TOP_K.

        Args:
            query: The raw (cleaned) query text.
            tickets: The list of retrieved tickets from FAISS, in cosine-similarity order.

        Returns:
            Re-ordered list, best cross-encoder match first, truncated to settings.rerank_top_k.
        """
        if not tickets:
            return tickets

        pairs = [(query, t.body) for t in tickets]
        ce_scores = self.model.predict(pairs)

        ranked = sorted(zip(ce_scores, tickets), key=lambda x: x[0], reverse=True)
        return [t for _, t in ranked[: settings.rerank_top_k]]
