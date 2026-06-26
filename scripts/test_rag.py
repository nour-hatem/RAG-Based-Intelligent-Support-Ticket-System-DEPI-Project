import sys
sys.path.insert(0, ".")

import pandas as pd
from src.models.ticket import Ticket
from src.services.embedding.embedder import Embedder
from src.services.retrieval.faiss_retriever import FAISSRetriever
from src.services.llm.groq_provider import GroqProvider
from src.services.rag.rag_pipeline import RAGPipeline


def main():
    pipeline = RAGPipeline(
        embedder=Embedder(),
        retriever=FAISSRetriever(),
        llm_provider=GroqProvider(),
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

        print(f"\nPredicted Queue  : {response.predicted_queue}")
        print(f"Generated Answer : {response.generated_answer[:300]}...")
        print(f"\nRetrieved {len(response.retrieved_documents)} tickets:")
        for doc in response.retrieved_documents:
            print(f"  [{doc.score:.4f}] {doc.queue:35s} | {doc.body[:60]}...")


if __name__ == "__main__":
    main()