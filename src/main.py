import logging
import secrets
import time
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Request, Security, status
from fastapi.security.api_key import APIKeyHeader
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from src.config import settings
from src.api.schemas import TicketRequest, TicketResponse
from src.models.ticket import Ticket
from src.services.embedding.embedder import Embedder
from src.services.retrieval.faiss_retriever import FAISSRetriever
from src.services.llm.groq_provider import GroqProvider
from src.services.rerank.cross_encoder_reranker import CrossEncoderReranker
from src.services.rag.rag_pipeline import RAGPipeline, LLMParsingError

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


# ---------------------------------------------------------------------------
# Lifespan: build all heavy objects once at startup, store on app.state
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    t0 = time.perf_counter()
    logger.info("Starting up - loading models...")

    embedder = Embedder()
    logger.info("  [1/4] Embedder loaded")

    retriever = FAISSRetriever()
    logger.info("  [2/4] FAISS retriever loaded")

    llm_provider = GroqProvider()
    logger.info("  [3/4] Groq provider ready")

    reranker = None
    if settings.rerank_enabled:
        reranker = CrossEncoderReranker()
        logger.info("  [4/4] Cross-encoder reranker loaded")
    else:
        logger.info("  [4/4] Cross-encoder reranker skipped (RERANK_ENABLED=False)")

    app.state.rag_pipeline = RAGPipeline(
        embedder=embedder,
        retriever=retriever,
        llm_provider=llm_provider,
        reranker=reranker,
    )

    elapsed = time.perf_counter() - t0
    logger.info(f"Startup complete in {elapsed:.2f}s - ready to serve requests")

    yield  # application runs here

    logger.info("Shutting down")


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="RAG-Based Intelligent Support Ticket System",
    description="Classifies support tickets into queues and generates customer-facing answers using RAG.",
    version="0.1.0",
    lifespan=lifespan,
)

# The frontend (served from a different origin than the API, e.g. a local
# static file server or the deployed Azure Static Web App) needs the browser
# to be allowed to call this API cross-origin. Without this, /health and
# /api/v1/tickets/respond calls from the browser are blocked by CORS even
# though the API itself works fine (e.g. via curl or pytest).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=False,
    allow_methods=["*"], 
    allow_headers=["*"], 
)


# ---------------------------------------------------------------------------
# Exception handlers
# ---------------------------------------------------------------------------

@app.exception_handler(LLMParsingError)
async def llm_parsing_error_handler(request: Request, exc: LLMParsingError):
    # Log raw_response server-side only — never send it to the client
    logger.error(
        "LLMParsingError on %s %s: %s | raw_response: %r",
        request.method,
        request.url.path,
        str(exc),
        exc.raw_response,
    )
    return JSONResponse(
        status_code=502,
        content={
            "error": "bad_gateway",
            "detail": "The upstream language model returned an unparseable response. Please retry.",
        },
    )


@app.exception_handler(Exception)
async def generic_error_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "detail": "An unexpected error occurred. Please contact support if the problem persists.",
        },
    )


# ---------------------------------------------------------------------------
# Auth dependency
# ---------------------------------------------------------------------------

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(request: Request, api_key: str | None = Security(_api_key_header)) -> None:
    """Raises 401 if the X-API-Key header is missing or does not match settings.api_key.

    Uses secrets.compare_digest to avoid timing-based discrepancies.
    """
    if request.method == "OPTIONS":
            return

    if api_key is None or not secrets.compare_digest(api_key, settings.api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key.",
            headers={"WWW-Authenticate": "ApiKey"},
        )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/health", tags=["Health"])
async def health():
    """Public health check — no authentication required.

    Returns 200 when the app is running. Does not check model state (loading
    happens synchronously in the lifespan, so if the app is up, models are ready).
    """
    return {"status": "ok", "version": app.version}


@app.post(
    "/api/v1/tickets/respond",
    response_model=TicketResponse,
    tags=["Tickets"],
    summary="Classify a support ticket and generate a customer-facing response",
    dependencies=[Depends(verify_api_key)],
)
async def respond_to_ticket(request: Request, body: TicketRequest):
    """Accepts a support ticket, runs it through the RAG pipeline, and returns
    a predicted queue and generated answer (or flags it for human review if
    retrieval confidence is below the configured threshold).
    """
    ticket = Ticket(subject=body.subject, body=body.body)
    rag_response = request.app.state.rag_pipeline.run(ticket)

    return TicketResponse(
        predicted_queue=rag_response.predicted_queue,
        generated_answer=rag_response.generated_answer,
        needs_human_review=rag_response.needs_human_review,
        confidence_score=rag_response.confidence_score,
    )
