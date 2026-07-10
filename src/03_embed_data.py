"""
03_embed_data.py — Stage 3: Sentence Embedding Generation
==========================================================

Reads ``cleaned_corpus.csv``, encodes the ``clean_body`` column using
``all-MiniLM-L6-v2`` from SentenceTransformers, and saves the resulting
384-dimensional L2-normalised embeddings as a NumPy array.

L2 normalization means cosine similarity reduces to a dot product, which
is the default expected by FAISS and Azure Cognitive Search in downstream
milestones.

Usage
-----
    python src/03_embed_data.py
    python src/03_embed_data.py --input data/processed/cleaned_corpus.csv \\
                                --output-dir data/processed \\
                                --model all-MiniLM-L6-v2 \\
                                --batch-size 64

Outputs
-------
    data/processed/body_embeddings.npy   — shape (N, 384), dtype float32
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import pandas as pd

from src.utils.io_utils import save_embeddings, setup_output_dir

LOG_FMT = "%(asctime)s [%(levelname)s] %(name)s — %(message)s"
DATE_FMT = "%Y-%m-%d %H:%M:%S"
logger = logging.getLogger(__name__)


def _configure_logging() -> None:
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    handlers: list[logging.Handler] = [
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(log_dir / "03_embed_data.log", encoding="utf-8"),
    ]
    logging.basicConfig(level=logging.INFO, format=LOG_FMT, datefmt=DATE_FMT,
                        handlers=handlers)


# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------

def generate_embeddings(
    texts: list[str],
    model_name: str = "all-MiniLM-L6-v2",
    batch_size: int = 64,
    normalize: bool = True,
) -> np.ndarray:
    """Encode *texts* into dense sentence embeddings.

    Parameters
    ----------
    texts:
        List of cleaned text strings to encode.
    model_name:
        SentenceTransformer model identifier.  Defaults to
        ``"all-MiniLM-L6-v2"`` (384 dimensions, 512-token limit).
    batch_size:
        Number of texts per encoding batch.  Larger values are faster
        but require more GPU/CPU memory.
    normalize:
        If ``True`` (default), L2-normalise each embedding vector so that
        cosine similarity equals the dot product.  Required by FAISS and
        Azure Cognitive Search.

    Returns
    -------
    np.ndarray
        Float32 array of shape ``(len(texts), embedding_dim)``.

    Raises
    ------
    ImportError
        If ``sentence_transformers`` is not installed.
    """
    from sentence_transformers import SentenceTransformer  # deferred import

    logger.info("Loading SentenceTransformer model: %s", model_name)
    model = SentenceTransformer(model_name)

    logger.info(
        "Encoding %d texts  batch_size=%d  normalize=%s …",
        len(texts), batch_size, normalize,
    )
    embeddings: np.ndarray = model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=normalize,
    )

    logger.info("Encoding complete — shape=%s  dtype=%s", embeddings.shape, embeddings.dtype)

    # Sanity: verify first vector is unit-norm when normalization is on
    if normalize:
        first_norm = float(np.linalg.norm(embeddings[0]))
        if abs(first_norm - 1.0) > 1e-5:
            logger.warning(
                "First embedding norm is %.6f (expected ~1.0). "
                "Normalization may not have applied correctly.",
                first_norm,
            )
        else:
            logger.info("Norm check — first vector norm: %.6f ✓", first_norm)

    return embeddings


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Stage 3 — Generate sentence embeddings for clean_body.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--input",
        default="data/processed/cleaned_corpus.csv",
        help="Path to cleaned_corpus.csv produced by 02_clean_data.py.",
    )
    parser.add_argument(
        "--output-dir",
        default="data/processed",
        help="Directory to write body_embeddings.npy into.",
    )
    parser.add_argument(
        "--model",
        default="all-MiniLM-L6-v2",
        help="SentenceTransformer model name or path.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=64,
        help="Encoding batch size.",
    )
    parser.add_argument(
        "--no-normalize",
        action="store_true",
        help="Disable L2 normalization of embeddings.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    _configure_logging()
    output_dir = setup_output_dir(args.output_dir)

    logger.info("=== Stage 3: Embedding Generation ===")
    logger.info("Input      : %s", args.input)
    logger.info("Output dir : %s", output_dir)
    logger.info("Model      : %s", args.model)
    logger.info("Batch size : %d", args.batch_size)
    logger.info("Normalize  : %s", not args.no_normalize)

    logger.info("Loading corpus …")
    df = pd.read_csv(args.input)
    logger.info("Corpus loaded — %d rows.", len(df))

    if "clean_body" not in df.columns:
        logger.error(
            "'clean_body' column not found in %s. "
            "Run 02_clean_data.py first.",
            args.input,
        )
        sys.exit(1)

    texts = df["clean_body"].tolist()
    embeddings = generate_embeddings(
        texts,
        model_name=args.model,
        batch_size=args.batch_size,
        normalize=not args.no_normalize,
    )

    out_path = output_dir / "body_embeddings.npy"
    save_embeddings(embeddings, out_path, label="body_embeddings")

    logger.info("Stage 3 complete. Output: %s", out_path)


if __name__ == "__main__":
    main()
