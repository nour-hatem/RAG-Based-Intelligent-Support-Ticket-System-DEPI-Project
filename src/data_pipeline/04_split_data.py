"""
04_split_data.py — Stage 4: Stratified Train/Val/Test Split
============================================================

Reads ``cleaned_corpus.csv`` and ``body_embeddings.npy``, performs a
stratified 70/15/15 split on the ``queue`` column, slices the embeddings
in sync, and writes six output files.

The embeddings are sliced **before** the DataFrame index is reset so that
row alignment between CSVs and ``.npy`` files is always guaranteed.

Usage
-----
    python src/data_pipeline/04_split_data.py
    python src/data_pipeline/04_split_data.py --input-csv data/processed/cleaned_corpus.csv \\
                                --input-emb data/processed/body_embeddings.npy \\
                                --output-dir data/processed \\
                                --val-size 0.15 --test-size 0.15 --seed 42

Outputs (all under ``data/processed/``)
-------
    train.csv            val.csv            test.csv
    train_embeddings.npy val_embeddings.npy test_embeddings.npy
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import numpy as np
import pandas as pd

from src.utils.io_utils import save_dataframe, save_embeddings, setup_output_dir
from src.utils.split_utils import stratified_split

LOG_FMT = "%(asctime)s [%(levelname)s] %(name)s — %(message)s"
DATE_FMT = "%Y-%m-%d %H:%M:%S"
logger = logging.getLogger(__name__)


def _configure_logging() -> None:
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    handlers: list[logging.Handler] = [
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(log_dir / "04_split_data.log", encoding="utf-8"),
    ]
    logging.basicConfig(level=logging.INFO, format=LOG_FMT, datefmt=DATE_FMT,
                        handlers=handlers)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Stage 4 — Stratified 70/15/15 split of corpus and embeddings.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--input-csv",
        default="data/processed/cleaned_corpus.csv",
        help="Path to cleaned_corpus.csv produced by 02_clean_data.py.",
    )
    parser.add_argument(
        "--input-emb",
        default="data/processed/body_embeddings.npy",
        help="Path to body_embeddings.npy produced by 03_embed_data.py.",
    )
    parser.add_argument(
        "--output-dir",
        default="data/processed",
        help="Directory to write split CSVs and embedding .npy files into.",
    )
    parser.add_argument(
        "--stratify-col",
        default="queue",
        help="Column to stratify on.",
    )
    parser.add_argument(
        "--val-size",
        type=float,
        default=0.15,
        help="Fraction of the full dataset to reserve for validation.",
    )
    parser.add_argument(
        "--test-size",
        type=float,
        default=0.15,
        help="Fraction of the full dataset to reserve for testing.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    _configure_logging()
    output_dir = setup_output_dir(args.output_dir)

    logger.info("=== Stage 4: Train / Val / Test Split ===")
    logger.info("Input CSV  : %s", args.input_csv)
    logger.info("Input emb  : %s", args.input_emb)
    logger.info("Output dir : %s", output_dir)
    logger.info(
        "Split      : train=%.0f%%  val=%.0f%%  test=%.0f%%",
        (1 - args.val_size - args.test_size) * 100,
        args.val_size * 100,
        args.test_size * 100,
    )
    logger.info("Seed       : %d", args.seed)

    # Load inputs
    logger.info("Loading corpus …")
    df = pd.read_csv(args.input_csv)
    logger.info("Corpus loaded — %d rows, %d columns.", len(df), len(df.columns))

    logger.info("Loading embeddings …")
    embeddings = np.load(args.input_emb)
    logger.info("Embeddings loaded — shape=%s  dtype=%s.", embeddings.shape, embeddings.dtype)

    if len(df) != len(embeddings):
        logger.error(
            "Row count mismatch: CSV has %d rows but embeddings has %d rows. "
            "Ensure both files were produced from the same corpus.",
            len(df), len(embeddings),
        )
        sys.exit(1)

    # Split
    train_df, val_df, test_df, train_emb, val_emb, test_emb = stratified_split(
        df,
        embeddings,
        stratify_col=args.stratify_col,
        val_size=args.val_size,
        test_size=args.test_size,
        seed=args.seed,
    )

    # Save CSVs
    save_dataframe(train_df, output_dir / "train.csv",  label="train")
    save_dataframe(val_df,   output_dir / "val.csv",    label="val")
    save_dataframe(test_df,  output_dir / "test.csv",   label="test")

    # Save embeddings
    save_embeddings(train_emb, output_dir / "train_embeddings.npy", label="train_embeddings")
    save_embeddings(val_emb,   output_dir / "val_embeddings.npy",   label="val_embeddings")
    save_embeddings(test_emb,  output_dir / "test_embeddings.npy",  label="test_embeddings")

    logger.info(
        "Stage 4 complete.  train=%d  val=%d  test=%d",
        len(train_df), len(val_df), len(test_df),
    )


if __name__ == "__main__":
    main()
