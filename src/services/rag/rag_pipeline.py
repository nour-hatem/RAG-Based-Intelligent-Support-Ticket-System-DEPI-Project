import json
import re
from src.config import settings
from src.models.ticket import Ticket
from src.models.rag_response import RAGResponse
from src.services.embedding.embedder import Embedder
from src.services.retrieval.faiss_retriever import FAISSRetriever
from src.services.llm.groq_provider import GroqProvider
from src.services.rag.prompt_builder import build_prompt
from src.utils.helpers import clean_text


class RAGPipeline:
    def __init__(self):
        self.embedder = Embedder()
        self.retriever = FAISSRetriever()
        self.llm = GroqProvider()

    def run(self, ticket: Ticket) -> RAGResponse:
        query_embedding = self.embedder.embed(clean_text(ticket.body))
        retrieved = self.retriever.retrieve(query_embedding, top_k=settings.top_k)
        prompt = build_prompt(ticket, retrieved)
        raw_response = self.llm.generate(prompt)
        parsed = self._parse_response(raw_response)

        return RAGResponse(
            predicted_queue=parsed["predicted_queue"],
            generated_answer=parsed["generated_answer"],
            retrieved_documents=retrieved,
        )

    def _parse_response(self, raw: str) -> dict:
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if not match:
            raise ValueError(f"No JSON object found in LLM response: {raw}")
        try:
            return json.loads(match.group())
        except json.JSONDecodeError as e:
            raise ValueError(f"LLM returned invalid JSON: {e}\nRaw response: {raw}")