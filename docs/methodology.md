# Methodology

This document outlines the end-to-end methodology employed in building the Intelligent Support Ticket System, detailing the data pipeline, the baseline machine learning approach, and the final Retrieval-Augmented Generation (RAG) architecture.

## 1. Data Pipeline and Preprocessing
The foundation of any NLP system is data quality. We utilized a dataset of ~61,800 customer support tickets. To ensure high-quality input for both the baseline models and the RAG system, the data underwent a rigorous, automated pipeline:

- **Language Filtering:** To prevent garbage tokens from degrading the English-optimized models, we strictly filtered for English tickets (relying on the reliable `language` column), removing ~30% of the dataset.
- **Quality Gates:** We validated that over 99% of unique ticket bodies mapped consistently to the same queue, confirming the `queue` column as a trustworthy classification target without label ambiguity.
- **Text Normalization:** We applied Unicode NFKC normalization, removed URLs and emails (to strip noise and PII), and converted text to lowercase. Digits were intentionally retained as they carry queue-specific signals (e.g., error codes, version numbers).
- **Extreme Length Filtering:** Tickets with a clean body length of fewer than 30 characters or more than 5,000 characters were dropped to remove outliers.
- **Tokenization Analysis:** We verified that <5% of tickets exceeded the 512-token limit of our embedding model, ensuring that standard truncation was safe without requiring complex chunking strategies.
- **Stratified Splitting:** Due to moderate class imbalance across the 15 distinct queues, a strict 70/15/15 stratified split (train/validation/test) was applied to ensure reliable per-class metrics.

## 2. Baseline Approach: Traditional Machine Learning
To quantify the value of the RAG system, we first established a robust traditional ML baseline for the queue classification task.

- **Feature Engineering:** We used TF-IDF on a lemmatized version of the ticket bodies (with custom domain stopwords removed via spaCy) to extract discriminative keyword features.
- **Model Selection:** We evaluated Logistic Regression, Random Forest, and a Linear Support Vector Machine (SVM). 
- **Why Linear SVM?** The Linear SVM was chosen as the primary baseline because it achieved the highest validation F1 score during tuning and the highest weighted test F1 (0.7311). Support Vector Machines are historically highly effective in high-dimensional, sparse feature spaces like TF-IDF text data, drawing clear linear decision boundaries between distinct vocabulary clusters.

## 3. The RAG Approach: Architecture and Justification
Rather than fine-tuning a massive classification model or an LLM—which is computationally expensive, prone to catastrophic forgetting, and difficult to update with new knowledge—we opted for a Retrieval-Augmented Generation (RAG) architecture.

### A. Embedding Model: `all-MiniLM-L6-v2`
- **What it is:** A lightweight sentence-transformer model that maps sentences into a 384-dimensional dense vector space.
- **Why it is appropriate:** It offers an exceptional balance of speed and semantic capture. Given that our EDA showed most tickets are under 512 tokens, this model can embed queries instantly with high semantic fidelity without the massive compute overhead of larger models.

### B. Vector Store: FAISS
- **What it is:** Facebook AI Similarity Search, an open-source library for efficient similarity search and clustering of dense vectors.
- **Why it is appropriate:** We require sub-millisecond retrieval of historical tickets to inform queue classification and draft generation. FAISS using `IndexFlatIP` (exact search via dot product on L2-normalized embeddings, which mathematically equates to cosine similarity) guarantees perfectly accurate retrieval for our scale without the infrastructure complexity of a dedicated vector database.

### C. Queue Prediction via Retrieval
Instead of passing features through a classification layer, the system predicts the queue dynamically:
- It retrieves the top $K$ most semantically similar historical tickets.
- The predicted queue is determined by a majority vote of these neighbors.
- **Why it is appropriate:** This approach allows the system to be updated instantly. If a new queue is added, we simply index new tickets into FAISS; no model retraining is required.

### D. LLM Generation: Llama 3.1 8B (via Groq)
- **What it is:** An open-weights large language model, served via the ultra-fast Groq API.
- **Why it is appropriate:** By providing the LLM with the context of similar, previously resolved tickets, we ground its generation in reality, drastically reducing hallucination. The 8B model is fast and capable enough to synthesize a professional response when given high-quality retrieved context.

### E. Human-in-the-Loop Fallback
- **What it is:** A configurable `CONFIDENCE_THRESHOLD`. If the top retrieved ticket's cosine similarity falls below this threshold, the system flags `needs_human_review`.
- **Why it is appropriate:** Automated systems fail. By explicitly recognizing low-confidence retrievals (e.g., short, ambiguous, or highly novel queries), the system fails safely, routing the ticket to a human rather than generating an irrelevant or misleading response with false confidence.
