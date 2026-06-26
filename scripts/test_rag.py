import sys
sys.path.insert(0, ".")

import pandas as pd
from src.config import settings
from src.models.ticket import Ticket
from src.services.embedding.embedder import Embedder
from src.services.retrieval.faiss_retriever import FAISSRetriever
from src.services.llm.groq_provider import GroqProvider
from src.services.rerank.cross_encoder_reranker import CrossEncoderReranker
from src.services.rag.rag_pipeline import RAGPipeline


def main():
    reranker = CrossEncoderReranker() if settings.rerank_enabled else None

    pipeline = RAGPipeline(
        embedder=Embedder(),
        retriever=FAISSRetriever(),
        llm_provider=GroqProvider(),
        reranker=reranker,
    )
    test_df = pd.read_csv("data/processed/test.csv")
    samples = test_df.sample(3, random_state=42)

    for _, row in samples.iterrows():
        ticket = Ticket(
            subject=row["subject"] if pd.notna(row.get("subject", None)) else None,
            body=str(row["body"]),
        )

        print("\n" + "=" * 70)
        print(f"Subject    : {ticket.subject}")
        print(f"Body       : {str(row['body'])[:200]}...")
        print(f"True Queue : {row['queue']}")

        response = pipeline.run(ticket)

        print(f"\nPredicted Queue    : {response.predicted_queue}")
        print(f"Confidence Score   : {response.confidence_score:.4f}")
        print(f"Needs Human Review : {response.needs_human_review}")
        if response.generated_answer is not None:
            print(f"Generated Answer   : {response.generated_answer[:300]}...")
        else:
            print("Generated Answer   : [abstained — no answer generated]")
        print(f"\nRetrieved {len(response.retrieved_documents)} tickets:")
        for doc in response.retrieved_documents:
            print(f"  [{doc.score:.4f}] {doc.queue:35s} | {doc.body[:60]}...")


if __name__ == "__main__":
    main()