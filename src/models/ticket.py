from pydantic import BaseModel, Field
from typing import Optional

class Ticket(BaseModel):
    subject: Optional[str] = None
    body: str = Field(..., min_length=1)

class RetrievedTicket(BaseModel):
    subject: Optional[str] = None
    body: str
    answer: str
    queue: str
    score: float = Field(..., ge=0.0, le=1.0)