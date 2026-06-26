import sys
sys.path.insert(0, ".")

from src.services.embedding.embedder import Embedder
from src.services.retrieval.faiss_retriever import FAISSRetriever
from src.services.llm.groq_provider import GroqProvider
from src.services.rag.rag_pipeline import RAGPipeline
from src.evaluation.evaluator import Evaluator


def main():
    pipeline = RAGPipeline(
        embedder=Embedder(),
        retriever=FAISSRetriever(),
        llm_provider=GroqProvider(),
    )
    evaluator = Evaluator(pipeline)
    results = evaluator.run()

    print("\n=== RAG Evaluation Results ===")
    print(f"Sample size  : {results['sample_size']}")
    print(f"Abstained    : {results['abstained']} ({results['abstention_rate']:.1%})")
    print(f"Model        : {results['model']}")
    print(f"Top-K        : {results['top_k']}")
    print(f"Threshold    : {results['confidence_threshold']}")
    print(f"\nQueue Classification:")
    print(f"  Accuracy    : {results['queue_metrics']['accuracy']}")
    print(f"  Weighted F1 : {results['queue_metrics']['weighted_f1']}")
    print(f"\nAnswer Generation (non-abstained only, n={results['answer_metrics']['scored_answers']}):")
    print(f"  Mean BLEU    : {results['answer_metrics']['mean_bleu']}")
    print(f"  Mean ROUGE-L : {results['answer_metrics']['mean_rouge_l']}")


if __name__ == "__main__":
    main()