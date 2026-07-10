from typing import Optional
from pydantic import BaseModel, Field

from src.models.ticket import RetrievedTicket

class RAGResponse(BaseModel):
    predicted_queue: str = Field(..., min_length=1)
    generated_answer: Optional[str] = None
    retrieved_documents: list[RetrievedTicket]
    needs_human_review: bool = False
    confidence_score: float = Field(..., ge=0.0, le=1.0)