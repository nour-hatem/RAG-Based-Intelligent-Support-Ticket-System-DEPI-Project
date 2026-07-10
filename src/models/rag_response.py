from pydantic import BaseModel, Field

from src.models.ticket import RetrievedTicket

class RAGResponse(BaseModel):
    predicted_queue: str = Field(..., min_length=1)
    generated_answer: str = Field(..., min_length=1)
    retrieved_documents: list[RetrievedTicket]