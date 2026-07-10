# RAG Pipeline & Backend API

Branch: `feature/backend-api`

## Background

This is a multi-part team project. The data pipeline and classical baselines were completed first. Then the core RAG system (`feature/rag-pipeline`) was built. This branch (`feature/backend-api`) wraps that pipeline in a production-ready FastAPI service with authentication, Docker containerization, abstention logic, and cross-encoder re-ranking.

## What this does

It provides a REST API that accepts customer support tickets, retrieves similar resolved tickets, and uses an LLM to predict the queue and generate a customer-facing answer:

```
POST /api/v1/tickets/respond
        |
        v
  Ticket validation (max length 5000) & API Key Auth
        |
        v
  clean_text + embed (all-MiniLM-L6-v2)
        |
        v
  FAISS search over train.csv embeddings (top-K)
        |
        v
  [Abstention Check] -> if confidence < 0.55, return needs_human_review=True
        |
        v
  [Optional Re-ranking] -> Cross-encoder sorts retrieved docs
        |
        v
  Prompt built from ticket + retrieved tickets
        |
        v
  Groq LLM (llama-3.1-8b-instant)
        |
        v
  { predicted_queue, generated_answer, needs_human_review, confidence_score }
```

The system is designed to be highly reliable: it catches bad LLM JSON with a custom `LLMParsingError` mapped to a 502 Bad Gateway, abstains from answering if retrieval similarity is too low, and is fully containerized.

## Critical design decision: index scope

The FAISS index is built only on `train.csv` (19,679 rows), not on `cleaned_corpus.csv` (28,113 rows, which also contains val and test data). Index position `i` corresponds to `train.csv` row `i`.

This is intentional. If the index included test data, retrieving a test ticket would surface itself with similarity 1.0, and the system would just be copying the answer instead of generalizing. Keeping the index limited to train data makes the evaluation an honest measure of how the system handles tickets it has never seen.

## Project structure

```
src/
├── api/
│   └── schemas.py              Pydantic external request/response models
├── config/
│   └── settings.py             Pydantic settings, loaded from .env
├── evaluation/
│   ├── evaluator.py            Runs pipeline over test set
│   └── metrics.py              F1, accuracy, BLEU, ROUGE-L
├── models/
│   ├── ticket.py               Ticket, RetrievedTicket schemas
│   └── rag_response.py         RAGResponse internal schema
├── services/
│   ├── embedding/
│   │   └── embedder.py         SentenceTransformer wrapper
│   ├── llm/
│   │   └── groq_provider.py    Groq implementation
│   ├── rag/
│   │   ├── prompt_builder.py   Builds the LLM prompt
│   │   └── rag_pipeline.py     Orchestrator: embed → retrieve → generate
│   ├── rerank/
│   │   └── cross_encoder_reranker.py Optional re-ranking step
│   └── retrieval/
│       └── faiss_retriever.py  FAISS search + corpus lookup
├── utils/
│   └── helpers.py              clean_text()
└── main.py                     FastAPI entrypoint with async lifespan

scripts/
├── evaluate_rag.py      Full evaluation run
├── generate_report.py   Builds baseline comparison report
└── test_rag.py          Smoke test on 3 sample tickets

tests/
└── test_api.py          Integration tests using FastAPI TestClient

reports/                 Test results and M3 completion reports
docs/                    Postman collection and project milestones

docker-compose.yml       Docker orchestration and volume mounting
Dockerfile               Multi-stage container definition
.dockerignore            Excludes raw data and local environments
pytest.ini               Pytest configuration (skips e2e by default)
requirements.txt         Python dependencies
.env.example             Template for environment variables
```

Each layer has one job. The LLM and the vector store are both behind interfaces, so swapping Groq for another provider or FAISS for another vector store later only means writing a new provider class, not touching the pipeline logic.

**FastAPI `main.py`** uses an async `@lifespan` context manager to load the Embedder, FAISS Index, Groq Provider, and Cross-Encoder exactly once at startup. The heavy ML models are stored on `app.state` to serve requests with minimal latency.

**Embedder** turns text into a normalized 384-dim vector using the same model and settings (`normalize_embeddings=True`) that built the FAISS index.

**FAISSRetriever** searches the index and pulls the matching rows from `train.csv`. Scores are clamped to `[0.0, 1.0]`.

**Abstention & Reranker** (in `rag_pipeline.py`): The pipeline checks if the top cosine similarity score is below `CONFIDENCE_THRESHOLD`. If so, it short-circuits and flags for human review to save LLM costs and prevent hallucinations. If confident, it optionally runs the `CrossEncoderReranker` to re-order the results before passing them to the prompt.

**PromptBuilder** assembles the retrieved tickets and the new ticket into a single prompt and instructs the LLM to return strict JSON.

**GroqProvider** calls the Groq API at `temperature=0.0` for consistent, repeatable output.

**Evaluator** runs the pipeline on a stratified sample from `test.csv` and computes queue F1/accuracy plus BLEU and ROUGE-L for the generated answers, gracefully handling abstentions.

## Setup

```bash
pip install -r requirements.txt
```

Create a `.env` file:

```
# Required
GROQ_API_KEY=your_key_here
API_KEY=local-dev-key

# Optional — defaults match settings.py
MODEL_NAME=llama-3.1-8b-instant
EMBED_MODEL=all-MiniLM-L6-v2
TOP_K=5
EVAL_SAMPLE_SIZE=250
FAISS_INDEX_PATH=faiss/faiss.index
TRAIN_CSV_PATH=data/processed/train.csv
TEST_CSV_PATH=data/processed/test.csv

# API server
HOST=0.0.0.0
PORT=8000

# Abstention
CONFIDENCE_THRESHOLD=0.55

# Cross-encoder re-ranking (disabled by default)
RERANK_ENABLED=False
RERANK_MODEL_NAME=cross-encoder/ms-marco-MiniLM-L-6-v2
RERANK_TOP_K=5
```

Required from the earlier pipeline stage, generated locally and not committed to git:

```
faiss/faiss.index
embeddings/train_embeddings.npy
data/processed/train.csv
data/processed/test.csv
```

## Running it (Docker - Recommended)

The application is fully dockerized. It mounts the `data/` and `faiss/` directories as read-only volumes and caches HuggingFace models in a Docker volume so they don't re-download.

```bash
docker compose up --build -d
```

The API will be available at `http://localhost:8000`. 

Check the health endpoint (no auth required):
```bash
curl http://localhost:8000/health
```

Test the main inference endpoint (auth required):
```bash
curl -X POST http://localhost:8000/api/v1/tickets/respond \
  -H "Content-Type: application/json" \
  -H "X-API-Key: local-dev-key" \
  -d '{"subject": "Cannot login", "body": "I forgot my password and the reset link is not working."}'
```

You can also import `docs/rag_support_ticket_api.postman_collection.json` into Postman to test all endpoints. Be sure to set the `api_key` collection variable.

## Running it (Local / Dev)

```bash
uvicorn src.main:app --host 0.0.0.0 --port 8000
```

Run tests and evaluation:
```bash
pytest tests/test_api.py -v       # API integration tests (mocks LLM)
RUN_E2E=true pytest -m e2e -v     # Run real LLM end-to-end test
python scripts/test_rag.py        # sanity check on 3 tickets
python scripts/evaluate_rag.py    # full evaluation, saves reports/
python scripts/generate_report.py # builds reports/rag_vs_baseline.md
```

## Results

Evaluated on a stratified sample of 250 tickets from the test set.

| Metric | Linear SVM (baseline) | RAG |
|---|---|---|
| Queue weighted F1 | 0.7311 | 0.7223 |
| Answer BLEU | not applicable | 0.4141 |
| Answer ROUGE-L | not applicable | 0.5922 |

Queue classification drops by about 1.2 percent compared to the dedicated SVM baseline. This is expected. The RAG system is not a trained classifier, it infers the queue from retrieved context, so a small accuracy cost in exchange for generated answers is a reasonable trade rather than a regression. Answer generation has no equivalent in the baseline, since it never produced customer-facing responses.

## Known limitations

**Likely near-duplicate tickets between train and test.** During the smoke test, one test ticket retrieved a train ticket with cosine similarity 1.0000, meaning a near-identical or templated ticket exists in both splits. This inflates retrieval metrics (consistent with the baseline stage's high Retrieval@5 of 0.9028) and should be noted as a dataset characteristic rather than a property of the retrieval system.

**Placeholder tokens can leak into generated answers.** The dataset contains unresolved placeholders such as `<tel_num>` in some ground-truth answers. When a retrieved ticket contains one, the LLM has occasionally copied it verbatim instead of writing a natural sentence. The prompt can be tightened to explicitly instruct the model to ignore placeholder tokens in retrieved context.

**Query and index text normalization now match.** Queries are passed through the same `clean_text()` normalization used upstream before embedding, keeping them consistent with how the indexed `clean_body` text was embedded.

## Next steps

The backend API is complete (Milestone 3). All endpoints, error handling, validation, and containerization requirements are met. The next step is **Milestone 4 (Frontend)** or **Milestone 5 (MLOps & Azure Deployment)**, where this Dockerized container will be pushed to an Azure Container Registry and deployed to Azure Web Apps, CI/CD will be configured via GitHub Actions, and an optional frontend UI will be built to interact with this API.