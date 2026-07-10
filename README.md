# RAG-Based Intelligent Support Ticket System

An end-to-end support ticket triage system that classifies incoming customer messages into the correct support queue, retrieves the most similar historical tickets using semantic search, and drafts a suggested reply using an LLM — deferring to a human agent whenever its own confidence is too low.

Built as a DEPI graduation capstone project, and deployed live on Azure Container Apps.

**Dataset:** [Tobi-Bueck/customer-support-tickets](https://huggingface.co/datasets/Tobi-Bueck/customer-support-tickets)

**Live demo:** https://triage-frontend.proudplant-cb7f23f0.eastus.azurecontainerapps.io

---

## Table of contents

- [What it does](#what-it-does)
- [Architecture](#architecture)
- [Repository structure](#repository-structure)
- [Model performance](#model-performance)
- [Tech stack](#tech-stack)
- [Running locally](#running-locally)
- [API reference](#api-reference)
- [Deployment (Azure Container Apps)](#deployment-azure-container-apps)
- [Configuration reference](#configuration-reference)
- [Known limitations](#known-limitations)

---

## What it does

A support agent (or an end user) types a customer's message into the Triage UI. The system then:

1. **Embeds** the message using a sentence-transformer model.
2. **Retrieves** the most semantically similar tickets from a FAISS vector index built from historical ticket data.
3. **Predicts** the correct support queue (e.g. *Technical Support*, *Billing and Payments*, *Returns and Exchanges*) based on the retrieved neighbors.
4. **Generates** a draft reply using an LLM (Groq / Llama 3.1), grounded in the retrieved tickets.
5. **Flags for human review** whenever the retrieval confidence falls below a threshold, instead of returning a low-confidence answer as if it were reliable.

The result for each ticket includes the predicted queue, a confidence score, a suggested reply, and a `needs_human_review` flag.

## Architecture

```
                     ┌─────────────────────────┐
   Browser  ───────▶ │   Frontend (Next.js)     │
   (public)          │   Container App          │
                     │                          │
                     │  • UI (React + HeroUI)   │
                     │  • GET /health  ─────────┼──────┐  (client-side, public)
                     │  • POST /api/tickets/    │      │
                     │    respond (server proxy)│      │
                     └────────────┬─────────────┘      │
                                  │ server-side only     │
                                  │ (API key attached     │
                                  │  here, never sent      │
                                  │  to the browser)       │
                                  ▼                        ▼
                     ┌─────────────────────────────────────┐
                     │        Backend (FastAPI)             │
                     │        Container App                 │
                     │                                       │
                     │  POST /api/v1/tickets/respond         │
                     │  GET  /health                         │
                     │                                       │
                     │  1. sentence-transformers embedding   │
                     │  2. FAISS similarity search            │
                     │  3. Confidence check vs. threshold      │
                     │  4. Groq LLM (Llama 3.1) → draft reply  │
                     └───────────────────┬───────────────────┘
                                          │
                                          ▼
                                   ┌─────────────┐
                                   │  Groq API    │
                                   │ (Llama 3.1)  │
                                   └─────────────┘
```

**Why the frontend proxies through its own server route instead of calling the backend directly from the browser:** the backend requires an `X-API-Key` header. Routing ticket submissions through a Next.js server-side route handler (`/api/tickets/respond`) keeps that key out of the browser-side JS bundle entirely — only the unauthenticated `/health` check is called directly from the client.

## Repository structure

```text
RAG-Based-Intelligent-Support-Ticket-System-DEPI-Project/
├── src/                       # Single source of truth for all Python code
│   ├── baseline_models/       # TF-IDF, MLFlow, Evaluation baselines
│   ├── data_pipeline/         # Data ingestion, cleaning, and splitting scripts
│   ├── config/                # Pydantic settings, loaded from .env
│   ├── evaluation/            # Evaluator and metrics logic
│   ├── models/                # Pydantic and data models (Ticket, RAGResponse)
│   ├── services/              # Core RAG, LLM, Embedder, and Retriever logic
│   └── utils/                 # Helper functions
│
├── backend-api/               # FastAPI service wrapper
│   ├── api/                   # FastAPI routers and schemas
│   ├── tests/                 # Pytest integration tests
│   ├── Dockerfile             # Container configuration
│   ├── main.py                # FastAPI application entrypoint
│   ├── pytest.ini             # Pytest configuration
│   └── requirements.txt       # Backend dependencies
│
├── frontend/                  # Self-contained Next.js UI application
│   ├── app/
│   ├── components/
│   ├── Dockerfile
│   └── package.json
│
├── data/                      # Processed datasets and embeddings
├── docs/                      # Project documentation
├── faiss/                     # FAISS vector index
├── model/                     # Baseline models (pickled)
├── plots/                     # Visualizations and confusion matrices
├── reports/                   # Evaluation reports
├── scripts/                   # Utility scripts (test_rag.py, evaluate_rag.py)
│
├── docker-compose.yml         # Docker orchestration
├── .dockerignore              # Excludes raw data from build contexts
├── .env.example               # Template for environment variables
└── README.md                  # This file
```

## Model performance

Evaluated in Milestone 2 on a held-out test set, comparing three baseline classifiers plus the retrieval quality of the FAISS index actually used in production.

### Classification (test set)

| Model | Accuracy | Precision | Recall | F1 (weighted) |
|---|---|---|---|---|
| Logistic Regression | 0.7003 | 0.7234 | 0.7003 | 0.6973 |
| Random Forest | 0.6815 | 0.7136 | 0.6815 | 0.6841 |
| **Linear SVM (selected)** | **0.7323** | **0.7417** | **0.7323** | **0.7311** |

Linear SVM was selected as the baseline — it had the highest validation F1 during tuning and the highest weighted test F1, evaluated once as a final tie-breaker per the project's model-selection protocol.

### Retrieval (FAISS, cosine similarity)

| Metric | Value |
|---|---|
| Retrieval@1 | 0.8179 |
| Retrieval@3 | 0.8717 |
| Retrieval@5 | 0.9028 |
| Retrieval@10 | 0.9417 |
| MRR@10 | 0.8532 |
| Mean top-1 cosine similarity | 0.9342 |

Retrieval@5 is weakest on **Sales and Pre-Sales** (0.7698) and **Human Resources** (0.7927), and strongest on **Billing and Payments** (0.9491) and **Technical Support** (0.9294) — reflecting how distinctly each queue's tickets cluster in embedding space.

The production system embeds with `sentence-transformers/all-MiniLM-L6-v2` and uses `IndexFlatIP` (cosine similarity on L2-normalized vectors) for retrieval, with a configurable confidence threshold (`CONFIDENCE_THRESHOLD`, default `0.55`) below which a ticket is routed to a human instead of receiving an automated reply.

## Tech stack

**Backend**
- FastAPI + Uvicorn
- sentence-transformers (`all-MiniLM-L6-v2`) for embeddings
- FAISS for vector similarity search
- Groq API (Llama 3.1 8B Instant) for answer generation
- Optional cross-encoder re-ranking (`cross-encoder/ms-marco-MiniLM-L-6-v2`, disabled by default)
- scikit-learn, MLflow (offline training/evaluation)

**Frontend**
- Next.js 15 (App Router), React 19
- HeroUI component library, Tailwind CSS
- TypeScript

**Infrastructure**
- Docker (multi-stage builds for both services)
- Azure Container Registry (ACR)
- Azure Container Apps (ACA), external ingress on both services
- GitHub for source control and team collaboration

## Running locally

Requires Docker Desktop.

```bash
git clone <backend-repo-url>
git clone <frontend-repo-url> frontend   # placed alongside backend-api/ at the repo root

cp backend-api/.env.example backend-api/.env
# then fill in GROQ_API_KEY and API_KEY in backend-api/.env

docker compose up --build
```

- Frontend: http://localhost:3000
- Backend: http://localhost:8000 (interactive docs at `/docs`)

The compose file builds the frontend with `NEXT_PUBLIC_API_URL=http://localhost:8000` and wires the backend's `API_KEY` into the frontend's server-side proxy automatically — no manual URL configuration needed for local development.

## API reference

### `POST /api/v1/tickets/respond`

Requires header `X-API-Key: <your key>`.

**Request**
```json
{
  "subject": "Login issue",
  "body": "I can't reset my password, the email never arrives."
}
```

**Response**
```json
{
  "predicted_queue": "Technical Support",
  "generated_answer": "We apologize for the login issue you're experiencing...",
  "needs_human_review": false,
  "confidence_score": 0.66
}
```

`body` is required (1–5000 characters). When `confidence_score` falls below `CONFIDENCE_THRESHOLD`, `needs_human_review` is `true` and the ticket is routed to a human agent instead of receiving an automated reply.

### `GET /health`

Unauthenticated. Returns `200 OK` once the embedding model and FAISS index have finished loading.

## Deployment (Azure Container Apps)

Both services run as independent Container Apps inside the same Container Apps Environment (`triage-aca-env`), backed by Azure Container Registry (`acrsupporttriage2026`), in resource group `rg-triage-rag`.

| Service | Container App | Ingress | Target port |
|---|---|---|---|
| Backend (FastAPI) | `rag-ticket-api` | external | 8000 |
| Frontend (Next.js) | `triage-frontend` | external | 3000 |

**Backend image** is built with the sentence-transformer model pre-downloaded at build time (not at container startup), so replicas start instantly with no external network dependency on first request. `data/processed/` and `faiss/` are copied into the image directly rather than mounted as volumes, since Azure Container Apps has no host bind-mount equivalent.

**Frontend image** is built with `output: "standalone"` and run on a minimal Node 20 Alpine image — Nginx isn't used because the app relies on a server-side Next.js route handler (the backend-key proxy), which requires a running Node process rather than a static file server.

**Important build-time vs. runtime distinction:** `NEXT_PUBLIC_API_URL` is a build-time value — it gets compiled directly into the client-side JS bundle, so it must be passed as a Docker `--build-arg` at image-build time, not set afterward as a Container App environment variable. `BACKEND_API_URL` and `BACKEND_API_KEY`, by contrast, are read at runtime inside the frontend's server-side route handler and can be updated via `az containerapp update --set-env-vars` without rebuilding the image.

Because this project runs on an academic Azure subscription with ACR Tasks disabled (`TasksOperationsNotAllowed`), images are built locally with `docker build` and pushed to ACR with `docker push`/`az acr login`, rather than using `az acr build`.

Minimum replicas are set to 1 on both apps to avoid cold starts and scale-to-zero delays for the live demo link.

## Configuration reference

Backend (`backend-api/.env`):

| Variable | Purpose |
|---|---|
| `GROQ_API_KEY` | Groq API key for LLM generation |
| `API_KEY` | Shared secret required in the `X-API-Key` header |
| `MODEL_NAME` | LLM used for generation (default `llama-3.1-8b-instant`) |
| `EMBED_MODEL` | Embedding model (default `all-MiniLM-L6-v2`) |
| `TOP_K` | Number of neighbors retrieved per query |
| `CONFIDENCE_THRESHOLD` | Below this similarity score, a ticket is flagged `needs_human_review` |
| `CORS_ALLOW_ORIGINS` | Allowed frontend origin(s) |
| `RERANK_ENABLED` | Enables cross-encoder re-ranking of retrieved results |

Frontend (Container App environment variables):

| Variable | Read at | Purpose |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | build time | Base URL used by the client-side `/health` check |
| `BACKEND_API_URL` | runtime | Base URL the server-side proxy route forwards ticket submissions to |
| `BACKEND_API_KEY` | runtime | API key attached server-side to outgoing backend requests |

## Known limitations

- **Non-English input:** the embedding model and training data are English-only, so messages in Arabic or other languages tend to retrieve with low confidence and are routed to human review rather than misclassified with false confidence.
- **Short/ambiguous messages** (e.g. "it's not working") retrieve with lower confidence by design — this is the confidence threshold doing its job, not a bug.
- **Cold cache on scale-out:** new replicas re-download the HuggingFace model cache unless a persistent volume is attached; currently mitigated by baking the model into the image and keeping `min-replicas: 1`.
