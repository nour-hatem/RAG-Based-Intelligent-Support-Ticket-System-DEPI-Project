"""
Integration tests for the FastAPI HTTP layer (tests/test_api.py).

Strategy
--------
Most tests mock GroqProvider.generate() so they run fast, cost nothing, and are
deterministic. The RAG pipeline, embedder, FAISS retriever, and all real local
components still run — only the outbound Groq call is stubbed.

One real end-to-end test (marked with @pytest.mark.e2e) calls the actual Groq
API. It is excluded from the default test run; opt-in with:

    pytest -m e2e
    # or
    RUN_E2E=true pytest
"""

import json
import os
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from src.config import settings
from main import app

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def client():
    """Spin up the full app (real embedder + FAISS) once per module."""
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def auth_headers():
    """Valid API key header, read from the same settings object used by the app."""
    return {"X-API-Key": settings.api_key}


# A valid LLM JSON response returned by the mock
VALID_LLM_JSON = json.dumps({
    "predicted_queue": "Billing and Payments",
    "generated_answer": "We will look into the duplicate charge and process a refund within 3-5 business days.",
})

VALID_TICKET_BODY = {
    "subject": "Charged twice",
    "body": "I was charged twice for my subscription this month. Please refund the duplicate.",
}


# ---------------------------------------------------------------------------
# Auth tests — no LLM call needed
# ---------------------------------------------------------------------------

def test_health_no_auth(client):
    """GET /health must return 200 without any authentication header."""
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "version" in data


def test_respond_missing_api_key(client):
    """POST without X-API-Key header must return 401."""
    resp = client.post("/api/v1/tickets/respond", json=VALID_TICKET_BODY)
    assert resp.status_code == 401
    assert "Invalid or missing" in resp.json()["detail"]


def test_respond_wrong_api_key(client):
    """POST with an incorrect X-API-Key must return 401."""
    resp = client.post(
        "/api/v1/tickets/respond",
        json=VALID_TICKET_BODY,
        headers={"X-API-Key": "definitely-not-the-right-key"},
    )
    assert resp.status_code == 401
    assert "Invalid or missing" in resp.json()["detail"]


# ---------------------------------------------------------------------------
# Validation tests — no LLM call needed
# ---------------------------------------------------------------------------

def test_respond_oversized_body(client, auth_headers):
    """POST with a body exceeding 5000 chars must return 422 from Pydantic."""
    resp = client.post(
        "/api/v1/tickets/respond",
        json={"body": "x" * 5001},
        headers=auth_headers,
    )
    assert resp.status_code == 422
    errors = resp.json()["detail"]
    assert any("5000" in str(e) for e in errors)


def test_respond_empty_body(client, auth_headers):
    """POST with an empty body string must return 422 (min_length=1)."""
    resp = client.post(
        "/api/v1/tickets/respond",
        json={"body": ""},
        headers=auth_headers,
    )
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Normal path — mock LLM
# ---------------------------------------------------------------------------

def test_respond_valid_ticket_mocked_llm(client, auth_headers):
    """Valid authenticated request returns 200 with the correct response shape."""
    with patch("src.services.llm.groq_provider.GroqProvider.generate", return_value=VALID_LLM_JSON):
        resp = client.post(
            "/api/v1/tickets/respond",
            json=VALID_TICKET_BODY,
            headers=auth_headers,
        )

    assert resp.status_code == 200
    data = resp.json()
    assert "predicted_queue" in data
    assert "generated_answer" in data
    assert "needs_human_review" in data
    assert "confidence_score" in data
    assert isinstance(data["needs_human_review"], bool)
    assert isinstance(data["confidence_score"], float)
    assert 0.0 <= data["confidence_score"] <= 1.0


# ---------------------------------------------------------------------------
# Abstention path — mock retriever to return low similarity score
# ---------------------------------------------------------------------------

def test_respond_abstention_low_confidence(client, auth_headers):
    """When top retrieval score is below the threshold, needs_human_review=True
    and generated_answer=None must be returned without calling the LLM."""
    from src.models.ticket import RetrievedTicket

    low_score_doc = RetrievedTicket(
        subject=None,
        body="Some loosely related ticket body.",
        answer="Some answer.",
        queue="General Inquiry",
        score=0.10,   # well below the default 0.55 threshold
    )

    with patch("src.services.retrieval.faiss_retriever.FAISSRetriever.retrieve",
               return_value=[low_score_doc]) as mock_retrieve, \
         patch("src.services.llm.groq_provider.GroqProvider.generate") as mock_llm:

        resp = client.post(
            "/api/v1/tickets/respond",
            json=VALID_TICKET_BODY,
            headers=auth_headers,
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["needs_human_review"] is True
    assert data["generated_answer"] is None
    assert data["confidence_score"] == pytest.approx(0.10, abs=1e-4)
    # LLM must NOT have been called on the abstention path
    mock_llm.assert_not_called()


# ---------------------------------------------------------------------------
# LLMParsingError path — mock LLM to return garbage
# ---------------------------------------------------------------------------

def test_respond_llm_parsing_error_returns_502(client, auth_headers):
    """When the LLM returns unparseable output, the API must return 502, not 500."""
    with patch("src.services.llm.groq_provider.GroqProvider.generate",
               return_value="This is not JSON at all!!! ¯\\_(ツ)_/¯"):
        resp = client.post(
            "/api/v1/tickets/respond",
            json=VALID_TICKET_BODY,
            headers=auth_headers,
        )

    assert resp.status_code == 502
    data = resp.json()
    assert data["error"] == "bad_gateway"
    # Must not leak raw LLM output to the client
    assert "This is not JSON" not in resp.text
    assert "raw_response" not in resp.text


# ---------------------------------------------------------------------------
# Real end-to-end test (opt-in only)
# ---------------------------------------------------------------------------

@pytest.mark.e2e
@pytest.mark.skipif(
    not os.getenv("RUN_E2E"),
    reason="End-to-end test skipped. Set RUN_E2E=true to run against the real Groq API.",
)
def test_respond_real_groq_end_to_end(client, auth_headers):
    """Calls the real Groq API. Only runs when RUN_E2E=true is set.
    Not included in routine CI runs — it costs money and is nondeterministic.
    """
    resp = client.post(
        "/api/v1/tickets/respond",
        json={
            "subject": "Cannot access account",
            "body": (
                "I have been unable to log in to my account for the past two days. "
                "I tried resetting my password but the reset email never arrived. "
                "Please help me regain access as soon as possible."
            ),
        },
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["predicted_queue"] is not None
    assert isinstance(data["needs_human_review"], bool)
    assert 0.0 <= data["confidence_score"] <= 1.0
    if not data["needs_human_review"]:
        assert data["generated_answer"] is not None
        assert len(data["generated_answer"]) > 10
