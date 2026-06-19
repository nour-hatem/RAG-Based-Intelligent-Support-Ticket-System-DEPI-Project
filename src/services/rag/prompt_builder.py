from src.models.ticket import Ticket, RetrievedTicket

VALID_QUEUES = [
    "Billing and Payments",
    "Customer Service",
    "General Inquiry",
    "Human Resources",
    "IT Support",
    "Product Support",
    "Returns and Exchanges",
    "Sales and Pre-Sales",
    "Service Outages and Maintenance",
    "Technical Support",
]

queues_str = "\n".join(f"  - {q}" for q in VALID_QUEUES)


def build_prompt(ticket: Ticket, retrieved: list[RetrievedTicket]) -> str:
    context_blocks = []
    for i, doc in enumerate(retrieved, 1):
        context_blocks.append(
            f"[Ticket {i}]\nQueue: {doc.queue}\nBody: {doc.body}\nAnswer: {doc.answer}"
        )

    context = "\n---\n".join(context_blocks)

    return f"""You are a customer support routing assistant.

Given a new support ticket and {len(retrieved)} similar resolved tickets as context,
return a JSON object with exactly two keys:
- "predicted_queue": one of the following queues:
{queues_str}
- "generated_answer": a helpful, concise response to the customer

Similar resolved tickets:
---
{context}
---

New ticket:
Subject: {ticket.subject or "N/A"}
Body: {ticket.body}

Respond ONLY with valid JSON. No explanation, no markdown, no extra text."""