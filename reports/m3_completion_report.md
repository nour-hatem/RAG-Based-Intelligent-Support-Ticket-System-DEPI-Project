# M3 Completion Report — Backend API

**Branch:** `feature/backend-api`
---

## Verification Runs

### `scripts/test_rag.py` (pipeline smoke test)
- **Result:** ✅ Exit code 0 — all 3 sample tickets processed correctly
- Predicted queues match true queues
- `confidence_score` and `needs_human_review` fields present on all responses
- RERANK_ENABLED=False (default) — no regression from phases 3/4

### `pytest tests/test_api.py` (HTTP layer integration tests)
- **Runner:** pytest 9.1.1 + pytest-asyncio 1.4.0
- **Result:** ✅ 8 passed, 1 deselected (e2e skipped), 0 failed — in 13.87s

| # | Test | Result |
|---|------|--------|
| 1 | `test_health_no_auth` | ✅ PASSED |
| 2 | `test_respond_missing_api_key` | ✅ PASSED |
| 3 | `test_respond_wrong_api_key` | ✅ PASSED |
| 4 | `test_respond_oversized_body` | ✅ PASSED |
| 5 | `test_respond_empty_body` | ✅ PASSED |
| 6 | `test_respond_valid_ticket_mocked_llm` | ✅ PASSED |
| 7 | `test_respond_abstention_low_confidence` | ✅ PASSED |
| 8 | `test_respond_llm_parsing_error_returns_502` | ✅ PASSED |
| 9 | `test_respond_real_groq_end_to_end` | ⏭ SKIPPED (opt-in, `RUN_E2E=true`) |

### Docker (`docker compose up`)
- **Result:** ⚠️ NOT VERIFIED IN THIS SESSION
- The Docker daemon is not running on this machine (`/var/run/docker.sock` not available).
- The Dockerfile, docker-compose.yml, and .dockerignore have been created and are structurally correct.
- The API was fully verified working locally with uvicorn (phases 5 & 6), which is the runtime behaviour the container replicates.
- **Action required:** Run `sudo systemctl start docker && docker compose up` to perform the container verification before declaring M4 readiness.

---

## M3 Checklist

| Item | Status | Location | Notes |
|------|--------|----------|-------|
| FastAPI app entrypoint (`src/main.py`) | ✅ Done | `src/main.py` | Modern `@asynccontextmanager` lifespan, not deprecated `on_event` |
| Single endpoint wired to `RAGPipeline.run()` | ✅ Done | `src/main.py:respond_to_ticket` | `POST /api/v1/tickets/respond` |
| External API Pydantic schemas (separate from internal models) | ✅ Done | `src/api/schemas.py` | `TicketRequest` (max_length=5000), `TicketResponse` — isolated from `src/models/` |
| Lifespan startup loading (no per-request model reloading) | ✅ Done | `src/main.py:lifespan` | All 3-4 services built once, stored on `app.state.rag_pipeline` |
| `LLMParsingError` mapped to clean HTTP 502 | ✅ Done | `src/main.py:llm_parsing_error_handler` | `raw_response` logged server-side only, never sent to client |
| Generic unhandled exceptions mapped to safe 500 | ✅ Done | `src/main.py:generic_error_handler` | No internal details leaked |
| Confidence threshold / abstention logic | ✅ Done | `src/services/rag/rag_pipeline.py` | `top_score < settings.confidence_threshold` short-circuits before LLM call |
| Abstention handled correctly in evaluator | ✅ Done | `src/evaluation/evaluator.py` | Abstained rows excluded from BLEU/ROUGE, counted for queue metrics if predicted_queue is present; `abstention_rate` reported |
| Cross-encoder re-ranking (toggleable) | ✅ Done | `src/services/rerank/cross_encoder_reranker.py` | Runs only after abstention check; FAISS cosine scores used exclusively for threshold; disabled by default (`RERANK_ENABLED=False`) |
| Re-ranking not interfering with abstention | ✅ Done | `src/services/rag/rag_pipeline.py` | Explicit comment + ordering enforces this constraint |
| Dockerfile | ✅ Done | `Dockerfile` | Multi-stage, CPU-only torch, data/faiss not baked in |
| docker-compose.yml with volume-mounted artifacts | ✅ Done | `docker-compose.yml` | `data/processed` and `faiss` mounted `:ro`; `hf_cache` named volume for model persistence |
| `.dockerignore` | ✅ Done | `.dockerignore` | Excludes `data/`, `faiss/`, `.env`, `__pycache__`, venvs |
| Docker container verified working | ⚠️ Pending | — | Docker daemon offline; containers not started in this session. Structurally correct; needs manual verification. |
| API key authentication on ticket endpoint | ✅ Done | `src/main.py:verify_api_key` | `secrets.compare_digest`, `APIKeyHeader`, 401 on mismatch |
| `/health` exempt from authentication | ✅ Done | `src/main.py` | `verify_api_key` dependency applied only to `respond_to_ticket` |
| `requirements.txt` fully up to date | ✅ Done | `requirements.txt` | Includes `fastapi`, `uvicorn[standard]`, `pytest`, `pytest-asyncio`, `httpx` |
| Automated API integration tests passing | ✅ Done | `tests/test_api.py` | 8 passed, 1 skipped (e2e) |
| Postman collection | ✅ Done | `docs/rag_support_ticket_api.postman_collection.json` | 6 requests; `api_key` and `base_url` as collection variables |
| Integration test report | ✅ Done | `reports/integration_test_report.md` | Full coverage, limitations documented |
| Input length validation (`max_length` on ticket body) | ✅ Done | `src/api/schemas.py` | `max_length=5000` on `TicketRequest.body`, returns 422 automatically |
| Placeholder token leakage prevention in LLM prompt | ✅ Done | `src/services/rag/prompt_builder.py` | Phase 0 fix, inherited from `feature/rag-pipeline` |
| Safe JSON parsing with custom exception | ✅ Done | `src/services/rag/rag_pipeline.py:LLMParsingError` | Dict-type validation, required-key check, raw response attached to exception |
| Dependency injection on `RAGPipeline` | ✅ Done | `src/services/rag/rag_pipeline.py` | Phase 2; all three services injected via constructor |

---

## Known Gaps

1. **Docker container not verified in this session.** The Docker daemon was unavailable (`/var/run/docker.sock` missing). All API behaviour was verified running natively with uvicorn across phases 5, 6, and 8. The Dockerfile and docker-compose are structurally correct. **Must run `sudo systemctl start docker && docker compose up` before treating Docker verification as complete.**

2. **Real end-to-end test (`RUN_E2E=true`) not run in routine CI.** This is intentional by design — the test exists and is gated behind an environment variable. It was not run during this session but is available.

3. **`httpx2` deprecation warning.** FastAPI TestClient emits `StarletteDeprecationWarning` about `httpx` being deprecated in favour of `httpx2`. This is a warning, not a failure. Downstream resolution depends on `httpx2` reaching a stable release.

---

## M3 Readiness Statement

**M3 (Backend) is functionally complete and ready for M4, with one outstanding verification step:**

✅ All backend features are implemented and tested at the code level.
✅ The full pytest suite passes (8/8 non-e2e tests).
✅ The pipeline smoke test passes.
✅ The Postman collection is ready for manual testing.
⚠️ **Docker container verification is pending** — start the Docker daemon and run `docker compose up` to close this gap.

Once the Docker container has been started and both `GET /health` and `POST /api/v1/tickets/respond` (with a valid `X-API-Key`) return correct responses from inside the container, this branch can be considered **100% M3-complete** and merged or moved to M4 (Azure Deployment).
