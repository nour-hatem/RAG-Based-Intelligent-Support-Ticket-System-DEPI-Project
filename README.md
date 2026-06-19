# RAG Pipeline

Branch: `feature/rag-pipeline`

## Background

This is a multi-part team project. The data pipeline and the classical baselines, embeddings, and FAISS index were already completed before this branch started. What's implemented here is the next phase: a RAG system built on top of that existing work.

## What this does

It retrieves similar resolved tickets from the training corpus and uses an LLM to predict the queue and generate a customer-facing answer for a new ticket:

```
New ticket (subject + body)
        |
        v
  clean_text + embed (all-MiniLM-L6-v2)
        |
        v
  FAISS search over train.csv embeddings (top-K)
        |
        v
  Prompt built from ticket + retrieved tickets
        |
        v
  Groq LLM (llama-3.1-8b-instant)
        |
        v
  { predicted_queue, generated_answer }
```

The system answers two questions per ticket: which queue should this go to, and what should the agent respond.

## Critical design decision: index scope

The FAISS index is built only on `train.csv` (19,679 rows), not on `cleaned_corpus.csv` (28,113 rows, which also contains val and test data). Index position `i` corresponds to `train.csv` row `i`.

This is intentional. If the index included test data, retrieving a test ticket would surface itself with similarity 1.0, and the system would just be copying the answer instead of generalizing. Keeping the index limited to train data makes the evaluation an honest measure of how the system handles tickets it has never seen.

## Project structure

```
src/
├── config/
│   └── settings.py            Pydantic settings, loaded from .env
├── models/
│   ├── ticket.py               Ticket, RetrievedTicket schemas
│   └── rag_response.py         RAGResponse schema
├── services/
│   ├── embedding/
│   │   └── embedder.py         SentenceTransformer wrapper, loaded once
│   ├── retrieval/
│   │   └── faiss_retriever.py  FAISS search + corpus lookup
│   ├── llm/
│   │   ├── llm_interface.py    Abstract LLM interface
│   │   └── groq_provider.py    Groq implementation
│   └── rag/
│       ├── prompt_builder.py   Builds the LLM prompt from ticket + context
│       └── rag_pipeline.py     Orchestrator: embed → retrieve → generate
├── evaluation/
│   ├── metrics.py               F1, accuracy, BLEU, ROUGE-L
│   └── evaluator.py             Runs the pipeline over a stratified test sample
└── utils/
    └── helpers.py                clean_text(), mirrors the preprocessing pipeline

scripts/
├── test_rag.py          Smoke test on 3 sample tickets
├── evaluate_rag.py      Full evaluation run, saves results to reports/
└── generate_report.py   Builds the RAG vs baseline comparison report

reports/
├── rag_evaluation_results.json
└── rag_vs_baseline.md
```

Each layer has one job. The LLM and the vector store are both behind interfaces, so swapping Groq for another provider or FAISS for another vector store later only means writing a new provider class, not touching the pipeline logic.

## Why each layer exists

**Embedder** turns text into a normalized 384-dim vector using the same model and settings (`normalize_embeddings=True`) that built the FAISS index. The model loads once at startup, not on every call.

**FAISSRetriever** searches the index and pulls the matching rows from `train.csv`. Scores are clamped to `[0.0, 1.0]` since cosine similarity should fall in that range but floating point noise can occasionally push values slightly outside it.

**PromptBuilder** assembles the retrieved tickets and the new ticket into a single prompt and instructs the LLM to return strict JSON with exactly two keys: `predicted_queue` and `generated_answer`.

**GroqProvider** calls the Groq API at `temperature=0.0` for consistent, repeatable output, since this is a classification-adjacent task rather than a creative one.

**RAGPipeline** is the only piece that knows about all the other pieces. It calls them in order and parses the LLM's JSON response, extracting the JSON object directly with a regex rather than relying on the model to fence its output a specific way.

**Evaluator** draws a stratified sample from `test.csv` (so every queue is represented), runs the full pipeline on each ticket, and computes queue F1/accuracy plus BLEU and ROUGE-L for the generated answers. Failed rows are skipped and excluded from the reported sample size rather than aborting the whole run.

## Setup

```bash
pip install -r requirements.txt
```

Create a `.env` file:

```
GROQ_API_KEY=your_key_here
MODEL_NAME=llama-3.1-8b-instant
EMBED_MODEL=all-MiniLM-L6-v2
TOP_K=5
EVAL_SAMPLE_SIZE=250
FAISS_INDEX_PATH=faiss/faiss.index
TRAIN_CSV_PATH=data/processed/train.csv
TEST_CSV_PATH=data/processed/test.csv
```

Required from the earlier pipeline stage, generated locally and not committed to git:

```
faiss/faiss.index
embeddings/train_embeddings.npy
data/processed/train.csv
data/processed/test.csv
```

## Running it

```bash
python scripts/test_rag.py        # sanity check on 3 tickets
python scripts/evaluate_rag.py    # full evaluation, saves reports/rag_evaluation_results.json
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

The pipeline is designed to sit behind a FastAPI layer without modification. The expected addition is a `src/routes/` package exposing a single endpoint that instantiates `RAGPipeline` and calls `.run()`, plus a `src/main.py` FastAPI app. No existing controller or service logic needs to change for that step.