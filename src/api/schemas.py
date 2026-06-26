from typing import Optional
from pydantic import BaseModel, Field


class TicketRequest(BaseModel):
    """External-facing request model for the API layer.

    Separate from the internal Ticket model in src/models/ticket.py.
    Enforces a max_length on body to prevent overloading the embedder
    or exceeding the LLM's context window.
    """

    subject: Optional[str] = None
    body: str = Field(..., min_length=1, max_length=5000)


class TicketResponse(BaseModel):
    """External-facing response model for the API layer.

    Separate from the internal RAGResponse in src/models/rag_response.py.
    Omits retrieved_documents and other internals not meant for clients.
    """

    predicted_queue: Optional[str]
    generated_answer: Optional[str]
    needs_human_review: bool
    confidence_score: float
