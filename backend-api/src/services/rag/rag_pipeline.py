import json
import re
from typing import Optional
from src.config import settings
from src.models.ticket import Ticket
from src.models.rag_response import RAGResponse
from src.services.embedding.embedder import Embedder
from src.services.retrieval.faiss_retriever import FAISSRetriever
from src.services.llm.groq_provider import GroqProvider
from src.services.rerank.cross_encoder_reranker import CrossEncoderReranker
from src.services.rag.prompt_builder import build_prompt
from src.utils.helpers import clean_text


class LLMParsingError(Exception):
    """Raised when the LLM response cannot be parsed into the expected JSON format."""

    def __init__(self, message: str, raw_response: str | None = None):
        super().__init__(message)
        self.raw_response = raw_response


class RAGPipeline:
    def __init__(
        self,
        embedder: Embedder,
        retriever: FAISSRetriever,
        llm_provider: GroqProvider,
        reranker: Optional[CrossEncoderReranker] = None,
    ):
        self.embedder = embedder
        self.retriever = retriever
        self.llm = llm_provider
        self.reranker = reranker

    def run(self, ticket: Ticket) -> RAGResponse:
        query_embedding = self.embedder.embed(clean_text(ticket.body))
        retrieved = self.retriever.retrieve(query_embedding, top_k=settings.top_k)

        top_score = retrieved[0].score if retrieved else 0.0

        # Abstention check - uses FAISS cosine score exclusively.
        # Re-ranking must NOT run before this: CE scores are not [0,1].
        if top_score < settings.confidence_threshold:
            return RAGResponse(
                predicted_queue=retrieved[0].queue if retrieved else "Unknown",
                generated_answer=None,
                retrieved_documents=retrieved,
                needs_human_review=True,
                confidence_score=top_score,
            )

        # Optional re-ranking - runs only after abstention check passes.
        prompt_docs = retrieved
        if settings.rerank_enabled and self.reranker is not None:
            prompt_docs = self.reranker.rerank(clean_text(ticket.body), retrieved)

        prompt = build_prompt(ticket, prompt_docs)
        raw_response = self.llm.generate(prompt)
        parsed = self._parse_response(raw_response)

        return RAGResponse(
            predicted_queue=parsed["predicted_queue"],
            generated_answer=parsed["generated_answer"],
            retrieved_documents=retrieved,
            needs_human_review=False,
            confidence_score=top_score,
        )

    def _parse_response(self, raw: str) -> dict:
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if not match:
            raise LLMParsingError("No JSON object found in LLM response", raw_response=raw)
        
        try:
            parsed = json.loads(match.group())
        except json.JSONDecodeError as e:
            raise LLMParsingError(f"Invalid JSON in LLM response: {e}", raw_response=raw)
            
        if not isinstance(parsed, dict):
            raise LLMParsingError("LLM response parsed to a non-dictionary object", raw_response=raw)
            
        if "predicted_queue" not in parsed or "generated_answer" not in parsed:
            raise LLMParsingError("Missing required keys in LLM response", raw_response=raw)
            
        return parsed