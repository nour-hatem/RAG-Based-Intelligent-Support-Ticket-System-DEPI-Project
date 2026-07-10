# Integration Test Report — Backend API (Phase 8)

**Branch:** `feature/backend-api`
**Date:** 2026-06-26
**Test file:** `tests/test_api.py`
**Runner:** pytest 8.4.1 via FastAPI `TestClient` (backed by `httpx`)

---

## Summary

| # | Test | Category | Result |
|---|------|----------|--------|
| 1 | `test_health_no_auth` | Auth — exempt | ✅ PASSED |
| 2 | `test_respond_missing_api_key` | Auth | ✅ PASSED |
| 3 | `test_respond_wrong_api_key` | Auth | ✅ PASSED |
| 4 | `test_respond_oversized_body` | Validation | ✅ PASSED |
| 5 | `test_respond_empty_body` | Validation | ✅ PASSED |
| 6 | `test_respond_valid_ticket_mocked_llm` | Normal path | ✅ PASSED |
| 7 | `test_respond_abstention_low_confidence` | Abstention path | ✅ PASSED |
| 8 | `test_respond_llm_parsing_error_returns_502` | Error handling | ✅ PASSED |
| 9 | `test_respond_real_groq_end_to_end` | E2E (opt-in) | ⏭ SKIPPED |

**Result: 8 passed, 1 deselected (e2e), 0 failed — in 10.94s**

---

## Test Design

### Strategy: Mock the LLM, keep everything else real

The `TestClient` uses FastAPI's `lifespan`, so all heavy services — `Embedder` (SentenceTransformer),
`FAISSRetriever` (FAISS index + `train.csv`), and `GroqProvider` — are fully constructed once at
module scope in the `client` fixture.

The only thing mocked in most tests is `GroqProvider.generate()`. This gives:
- Real embedding computation and cosine similarity scoring
- Real FAISS retrieval and abstention threshold logic
- Real JSON parsing and error handling
- Controlled, deterministic LLM output (or deliberate garbage for the 502 test)

### Why mock the LLM?
- Calling the real Groq API in CI is slow (~1-2s per call), costs tokens, and is nondeterministic.
- All logic under test (auth, validation, pipeline orchestration, error mapping) is exercised
  fully without a live LLM call.

---

## Test Details

### 1. `test_health_no_auth`
`GET /health` with no headers must return `200`. Verifies the auth dependency is NOT applied
to the health endpoint, as required by the phase 5/6 design.

### 2. `test_respond_missing_api_key`
`POST /api/v1/tickets/respond` with no `X-API-Key` header returns `401`.
Response body contains `"Invalid or missing"`.

### 3. `test_respond_wrong_api_key`
Same endpoint with a deliberately incorrect key value returns `401`.
Verifies `secrets.compare_digest` rejects mismatches correctly.

### 4. `test_respond_oversized_body`
Body of 5001 characters returns `422 Unprocessable Entity`.
Pydantic's `max_length=5000` constraint on `TicketRequest.body` fires automatically,
no custom error handling needed.

### 5. `test_respond_empty_body`
Empty string body (`""`) returns `422`. Validates the `min_length=1` lower bound.

### 6. `test_respond_valid_ticket_mocked_llm`
Authenticated request with a valid ticket body. LLM is mocked to return a well-formed
JSON response. Verifies the response shape: all four fields present
(`predicted_queue`, `generated_answer`, `needs_human_review`, `confidence_score`),
correct types, and `confidence_score` in `[0.0, 1.0]`.

### 7. `test_respond_abstention_low_confidence`
`FAISSRetriever.retrieve` is mocked to return a single document with `score=0.10`,
well below the `CONFIDENCE_THRESHOLD=0.55` default. Verifies:
- `needs_human_review=True`
- `generated_answer=None`
- `confidence_score ≈ 0.10`
- `GroqProvider.generate` was **not called** (abstention skips the LLM)

### 8. `test_respond_llm_parsing_error_returns_502`
LLM is mocked to return `"This is not JSON at all!!! ¯\\_(ツ)_/¯"`.
Verifies the `LLMParsingError` exception handler returns `502` with
`error: "bad_gateway"`, and that the raw LLM output does **not** appear in the
HTTP response body (server-side logging only).

### 9. `test_respond_real_groq_end_to_end` *(opt-in, skipped by default)*
Calls the actual Groq API with a realistic ticket about a login issue.
Gated behind `@pytest.mark.e2e` and `@pytest.mark.skipif(not os.getenv("RUN_E2E"))`.

To run:
```bash
RUN_E2E=true pytest -m e2e
```

---

## Postman Collection

`docs/rag_support_ticket_api.postman_collection.json` — import into Postman directly.

**Collection variables** (set once, applies to all requests):

| Variable | Default | Notes |
|---|---|---|
| `base_url` | `http://localhost:8000` | Change to deployed URL when needed |
| `api_key` | `local-dev-key` | Set to your `API_KEY` from `.env` |

**Included requests:**

| Request | Expected Status |
|---|---|
| GET /health | 200 |
| POST /respond — normal ticket | 200 |
| POST /respond — minimal body (`"Help."`) | 200 or 200 with abstention |
| POST /respond — oversized body | 422 |
| POST /respond — missing API key | 401 |
| POST /respond — wrong API key | 401 |

---

## Known Limitations

1. **E2E test excluded from routine runs.** `test_respond_real_groq_end_to_end` is skipped
   unless `RUN_E2E=true` is set. This is intentional — the test costs tokens, is nondeterministic,
   and requires a live GROQ_API_KEY.

2. **Module-scoped client loads real models.** The `client` fixture loads SentenceTransformer and
   FAISS at module initialization, which takes ~4s on a cold run. This is a one-time cost per
   `pytest` invocation, not per test.

3. **`httpx2` deprecation warning.** FastAPI's `TestClient` currently emits a
   `StarletteDeprecationWarning` about `httpx` being deprecated in favour of `httpx2`.
   This is a warning only and does not affect functionality. Will be resolved when
   `httpx2` is stable and pinned in requirements.

4. **No concurrent request tests.** Tests run sequentially and do not verify thread-safety
   of `app.state.rag_pipeline`. Since the pipeline is stateless per-request (no shared
   mutable state between calls), this is not expected to be an issue in practice.
