import numpy as np
from sentence_transformers import SentenceTransformer
from src.config import settings


class Embedder:
    def __init__(self):
        self.model = SentenceTransformer(settings.embed_model)

    def embed(self, texts: str | list[str]) -> np.ndarray:
        if isinstance(texts, str):
            texts = [texts]

        embeddings = self.model.encode(
            texts,
            batch_size=64,
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=True,  # L2-norm: dot product == cosine similarity
        )

        return embeddings.astype("float32")