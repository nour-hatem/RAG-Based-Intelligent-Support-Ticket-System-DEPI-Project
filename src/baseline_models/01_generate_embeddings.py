"""
Member 2 — Step 1: Embeddings Generation (MANDATORY)
========================================================
Model : SentenceTransformer('all-MiniLM-L6-v2')   — as required by spec
Run on: Google Colab (HuggingFace Hub reachable there)

Reads the Milestone 1 splits and produces 384-dim, L2-normalized
embeddings for the full corpus and each split. These are the inputs
consumed by 03_faiss_index.py for vector search.

Input:
    data/processed/cleaned_corpus.csv
    data/processed/train.csv
    data/processed/val.csv
    data/processed/test.csv

Output:
    embeddings/body_embeddings.npy   (N_full  x 384)
    embeddings/train_embeddings.npy  (19,679  x 384)
    embeddings/val_embeddings.npy    (4,217   x 384)
    embeddings/test_embeddings.npy   (4,217   x 384)
"""
import os
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer

BASE = "data/processed/"
OUT  = "embeddings/"
os.makedirs(OUT, exist_ok=True)

MODEL_NAME = "all-MiniLM-L6-v2"
TEXT_COL   = "clean_body"   # falls back to lemmatized_body if column is absent

print(f"Loading {MODEL_NAME} ...")
model = SentenceTransformer(MODEL_NAME)


def get_text(df: pd.DataFrame) -> list:
    col = TEXT_COL if TEXT_COL in df.columns else "lemmatized_body"
    return df[col].fillna("").astype(str).tolist()


def encode(texts: list, label: str) -> np.ndarray:
    print(f"Encoding {label}: {len(texts):,} rows ...")
    emb = model.encode(
        texts,
        batch_size=64,
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=True,   # L2-normalized -> cosine similarity == dot product
    )
    print(f"  -> shape {emb.shape}, dtype {emb.dtype}")
    return emb.astype("float32")


if __name__ == "__main__":
    full  = pd.read_csv(BASE + "cleaned_corpus.csv")
    train = pd.read_csv(BASE + "train.csv")
    val   = pd.read_csv(BASE + "val.csv")
    test  = pd.read_csv(BASE + "test.csv")

    full_emb  = encode(get_text(full),  "full corpus")
    train_emb = encode(get_text(train), "train")
    val_emb   = encode(get_text(val),   "val")
    test_emb  = encode(get_text(test),  "test")

    np.save(OUT + "body_embeddings.npy",  full_emb)
    np.save(OUT + "train_embeddings.npy", train_emb)
    np.save(OUT + "val_embeddings.npy",   val_emb)
    np.save(OUT + "test_embeddings.npy",  test_emb)

    print("\nSaved all embedding files to", OUT)
    print(f"  full : {full_emb.shape}")
    print(f"  train: {train_emb.shape}")
    print(f"  val  : {val_emb.shape}")
    print(f"  test : {test_emb.shape}")
