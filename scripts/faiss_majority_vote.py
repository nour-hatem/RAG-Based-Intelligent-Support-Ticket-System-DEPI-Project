import os
import sys
from collections import Counter
import pandas as pd
import numpy as np
from sklearn.metrics import accuracy_score, f1_score

sys.path.insert(0, os.path.abspath("."))
from src.services.retrieval.faiss_retriever import FAISSRetriever

def main():
    test_df = pd.read_csv("data/processed/test.csv")
    test_embs = np.load("embeddings/test_embeddings.npy").astype("float32")
    
    retriever = FAISSRetriever()
    y_true = []
    y_pred = []
    
    for i, row in test_df.iterrows():
        y_true.append(row["queue"])
        emb = test_embs[i:i+1] # shape (1, 384)
        
        scores, indices = retriever.index.search(emb, 5) # top-5
        
        queues = []
        for idx in indices[0]:
            if idx != -1:
                queues.append(retriever.corpus.iloc[idx]["queue"])
        
        if queues:
            # Majority vote
            most_common = Counter(queues).most_common(1)[0][0]
            y_pred.append(most_common)
        else:
            y_pred.append("Unknown")
            
    acc = accuracy_score(y_true, y_pred)
    f1 = f1_score(y_true, y_pred, average="weighted")
    
    print(f"FAISS Top-5 Majority Vote (n={len(test_df)}):")
    print(f"Accuracy: {acc:.4f}")
    print(f"Weighted F1: {f1:.4f}")

if __name__ == "__main__":
    main()
