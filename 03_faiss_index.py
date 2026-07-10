"""
Member 2 — Step 3: FAISS Index (MANDATORY + improved similarity metric)
===========================================================================
Builds a FAISS index on the REAL SentenceTransformer('all-MiniLM-L6-v2')
embeddings generated in step 1. No placeholder or alternative embedding
method is used anywhere in this script.

CHANGE IN THIS VERSION: IndexFlatL2 -> IndexFlatIP
----------------------------------------------------
The embeddings were generated with normalize_embeddings=True, i.e. every
vector has L2 norm == 1. For two unit vectors a and b:

    ||a - b||^2 = ||a||^2 + ||b||^2 - 2(a . b) = 1 + 1 - 2(a . b) = 2 - 2(a . b)

So L2 distance is a strictly decreasing function of the dot product a . b.
Ranking by smallest L2 distance and ranking by largest dot product produce
IDENTICAL orderings of nearest neighbors when vectors are unit-normalized.
The dot product of two unit vectors IS the cosine similarity by definition
(cosine_sim = a.b / (||a|| ||b||) = a.b / (1*1) = a.b). So IndexFlatIP on
these embeddings computes exact cosine similarity, while IndexFlatL2 was
computing a monotonic transform of the same thing — same neighbor ranking,
but:
  - IndexFlatIP returns scores directly interpretable as cosine similarity
    in [-1, 1] (in practice [0, 1] for this kind of text embedding),
    which is far easier to reason about and threshold than raw L2 distance.
  - It's the metric SentenceTransformer's own documentation recommends
    pairing with normalize_embeddings=True.
  - It avoids ambiguity for anyone reading the retrieval results later
    ("is 0.56 a good L2 distance?" vs "is 0.82 cosine similarity good?
     yes, obviously similar").
Ranking-wise this change does not alter which neighbors are retrieved
(it's a monotonic re-scoring of the same L2-based ranking), but it does
change the literal index type and the units of the returned scores, both
of which the spec calls for explicitly.

Input:
    embeddings/train_embeddings.npy   (19,679 x 384)
    embeddings/val_embeddings.npy     (4,217 x 384)
    embeddings/test_embeddings.npy    (4,217 x 384)

Output:
    faiss/faiss.index   (IndexFlatIP, persisted, built over train embeddings)
"""
import os
import numpy as np
import faiss

EMB = "embeddings/"
OUT = "faiss/"
os.makedirs(OUT, exist_ok=True)

train_emb = np.load(EMB + "train_embeddings.npy").astype("float32")
val_emb   = np.load(EMB + "val_embeddings.npy").astype("float32")
test_emb  = np.load(EMB + "test_embeddings.npy").astype("float32")

dim = train_emb.shape[1]
assert dim == 384, f"Expected 384-dim SentenceTransformer embeddings, got {dim}"

# Verify the normalization assumption the IP-as-cosine equivalence depends on.
norms = np.linalg.norm(train_emb, axis=1)
print(f"Embedding dim: {dim}, train vectors: {train_emb.shape[0]}")
print(f"Train embedding norms: min={norms.min():.4f} max={norms.max():.4f} mean={norms.mean():.4f}")
if not np.allclose(norms, 1.0, atol=1e-3):
    print("WARNING: embeddings are not unit-normalized — IndexFlatIP will NOT "
          "equal cosine similarity in this case. Re-run 01_generate_embeddings.py "
          "with normalize_embeddings=True, or normalize here before indexing.")

# IndexFlatIP — exact inner-product search. On L2-normalized vectors this
# IS cosine similarity (see derivation above). Replaces IndexFlatL2.
index = faiss.IndexFlatIP(dim)
index.add(train_emb)
print(f"FAISS index built (IndexFlatIP / cosine similarity): {index.ntotal} vectors")

faiss.write_index(index, OUT + "faiss.index")
print("Saved FAISS index to", OUT + "faiss.index")

# Sanity check: nearest neighbors for the first 3 validation tickets.
# Scores are now cosine similarities (higher = more similar), NOT distances.
D, I = index.search(val_emb[:3], k=5)
print("\nSanity check — nearest neighbors for first 3 val tickets (cosine similarity scores):")
for i in range(3):
    print(f"  query {i}: neighbors={I[i].tolist()}  cosine_sim={np.round(D[i], 4).tolist()}")
