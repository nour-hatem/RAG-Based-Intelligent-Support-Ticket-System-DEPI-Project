"""
02_clean_data.py — Stage 2: Language Filtering, Cleaning & Lemmatization
=========================================================================

Reads the raw CSV produced by ``01_load_data.py``, applies the full
text-preprocessing pipeline, and writes ``cleaned_corpus.csv``.

Steps
-----
1. Load ``raw.csv``
2. Filter to English rows (``language == "en"``)
3. Data quality checks (nulls, duplicates — logged, never printed)
4. Apply ``clean_text()`` to ``body`` and ``answer``
5. Drop rows with extreme body lengths
6. Lemmatize ``clean_body`` with spaCy ``en_core_web_sm``
7. Save ``cleaned_corpus.csv``

Usage
-----
    python src/02_clean_data.py
    python src/02_clean_data.py --input data/processed/raw.csv \\
                                --output-dir data/processed \\
                                --min-len 30 --max-len 5000

Outputs
-------
    data/processed/cleaned_corpus.csv
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd

from src.utils.io_utils import save_dataframe, setup_output_dir
from src.utils.text_utils import clean_text, lemmatize_corpus

LOG_FMT = "%(asctime)s [%(levelname)s] %(name)s — %(message)s"
DATE_FMT = "%Y-%m-%d %H:%M:%S"
logger = logging.getLogger(__name__)


def _configure_logging() -> None:
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    handlers: list[logging.Handler] = [
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(log_dir / "02_clean_data.log", encoding="utf-8"),
    ]
    logging.basicConfig(level=logging.INFO, format=LOG_FMT, datefmt=DATE_FMT,
                        handlers=handlers)


# ---------------------------------------------------------------------------
# Pipeline steps
# ---------------------------------------------------------------------------

def filter_language(df: pd.DataFrame, lang: str = "en") -> pd.DataFrame:
    """Keep only rows where ``language == lang``.

    Parameters
    ----------
    df:
        Raw DataFrame loaded from ``raw.csv``.
    lang:
        ISO 639-1 language code to keep.  Defaults to ``"en"``.

    Returns
    -------
    pd.DataFrame
        Filtered DataFrame with a reset index.
    """
    before = len(df)
    if "language" not in df.columns:
        logger.warning("No 'language' column found — skipping language filter.")
        return df

    distribution = df["language"].value_counts()
    logger.info("Language distribution before filter:\n%s", distribution.to_string())

    df = df[df["language"] == lang].reset_index(drop=True)
    removed = before - len(df)
    logger.info(
        "Language filter '%s' — removed %d rows, %d rows remain.",
        lang, removed, len(df),
    )
    return df


def quality_checks(df: pd.DataFrame) -> None:
    """Log null counts and duplicate statistics (no rows removed here).

    Parameters
    ----------
    df:
        DataFrame to inspect.
    """
    null_counts = df.isnull().sum()
    logger.info("Null counts per column:\n%s", null_counts[null_counts > 0].to_string()
                or "  (none)")

    full_dups = df.duplicated().sum()
    logger.info("Full-row duplicates: %d", full_dups)

    if "body" in df.columns:
        unique_bodies = df["body"].nunique()
        dup_bodies = len(df) - unique_bodies
        logger.info(
            "Unique body values: %d / %d total  (%d duplicate bodies)",
            unique_bodies, len(df), dup_bodies,
        )

        if "queue" in df.columns:
            body_multi_queue = (
                df.groupby("body")["queue"].nunique().gt(1).sum()
            )
            if body_multi_queue > 0:
                logger.warning(
                    "%d ticket body/bodies appear under multiple queues — "
                    "this may indicate label noise.",
                    body_multi_queue,
                )


def apply_cleaning(df: pd.DataFrame) -> pd.DataFrame:
    """Apply ``clean_text()`` to ``body`` and ``answer`` columns.

    Parameters
    ----------
    df:
        DataFrame containing at minimum a ``body`` column.

    Returns
    -------
    pd.DataFrame
        Input DataFrame with ``clean_body`` and ``clean_answer`` columns added.
    """
    logger.info("Cleaning 'body' column (%d rows) …", len(df))
    df["clean_body"] = df["body"].apply(clean_text)

    if "answer" in df.columns:
        logger.info("Cleaning 'answer' column …")
        df["clean_answer"] = df["answer"].apply(clean_text)
    else:
        logger.warning("No 'answer' column found — skipping answer cleaning.")

    return df


def filter_body_length(
    df: pd.DataFrame,
    min_len: int = 30,
    max_len: int = 5000,
) -> pd.DataFrame:
    """Drop rows where ``clean_body`` character length is outside ``[min_len, max_len]``.

    Parameters
    ----------
    df:
        DataFrame containing a ``clean_body`` column.
    min_len:
        Minimum number of characters required (inclusive).
    max_len:
        Maximum number of characters allowed (inclusive).

    Returns
    -------
    pd.DataFrame
        Filtered DataFrame with a reset index.
    """
    before = len(df)
    body_len = df["clean_body"].str.len()
    df = df[(body_len >= min_len) & (body_len <= max_len)].reset_index(drop=True)
    removed = before - len(df)
    logger.info(
        "Body length filter [%d, %d] — removed %d rows, %d remain.",
        min_len, max_len, removed, len(df),
    )
    return df


def add_length_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Add ``body_length``, ``answer_length``, and ``clean_answer_length`` columns.

    Parameters
    ----------
    df:
        Cleaned DataFrame.

    Returns
    -------
    pd.DataFrame
        DataFrame with length columns appended.
    """
    df["body_length"] = df["body"].str.len()
    if "answer" in df.columns:
        df["answer_length"] = df["answer"].str.len()
    if "clean_answer" in df.columns:
        df["clean_answer_length"] = df["clean_answer"].str.len()
    logger.debug("Length columns added.")
    return df


def apply_lemmatization(df: pd.DataFrame, batch_size: int = 256) -> pd.DataFrame:
    """Lemmatize ``clean_body`` using spaCy and add ``lemmatized_body`` column.

    Parameters
    ----------
    df:
        Cleaned DataFrame with a ``clean_body`` column.
    batch_size:
        spaCy pipe batch size.  Larger values trade RAM for speed.

    Returns
    -------
    pd.DataFrame
        DataFrame with ``lemmatized_body`` column added.
    """
    unique_texts = df["clean_body"].unique().tolist()
    lemma_map = lemmatize_corpus(unique_texts, batch_size=batch_size)
    df["lemmatized_body"] = df["clean_body"].map(lemma_map)
    logger.info("'lemmatized_body' column added.")

    # Sanity check — log a few examples
    for _, row in df.head(3).iterrows():
        logger.debug(
            "clean:      %s …\nlemmatized: %s …",
            str(row["clean_body"])[:110],
            str(row["lemmatized_body"])[:110],
        )
    return df


def build_corpus_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Select and order the columns for the final ``cleaned_corpus.csv``.

    Optional columns (``subject``, ``version``) are included only if they
    exist in the dataset, mirroring the original notebook logic.

    Parameters
    ----------
    df:
        Fully processed DataFrame.

    Returns
    -------
    pd.DataFrame
        Subset of *df* with the canonical corpus column order.
    """
    tag_cols = [c for c in df.columns if c.startswith("tag_")]

    base_cols = ["body", "answer", "type", "queue", "priority"]
    optional_cols = [c for c in ["subject", "version"] if c in df.columns]
    derived_cols = [
        "clean_body", "clean_answer", "lemmatized_body",
        "body_length", "answer_length", "clean_answer_length",
    ]

    # Insert optional cols before base cols (matches notebook ordering)
    keep_cols = optional_cols + base_cols + tag_cols + derived_cols
    # Only keep columns that actually exist
    keep_cols = [c for c in keep_cols if c in df.columns]
    logger.info("Corpus columns (%d): %s", len(keep_cols), keep_cols)
    return df[keep_cols]


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Stage 2 — Language filter, text cleaning, and lemmatization.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--input",
        default="data/processed/raw.csv",
        help="Path to the raw CSV produced by 01_load_data.py.",
    )
    parser.add_argument(
        "--output-dir",
        default="data/processed",
        help="Directory to write cleaned_corpus.csv into.",
    )
    parser.add_argument(
        "--min-len",
        type=int,
        default=30,
        help="Minimum clean_body character length (rows below are dropped).",
    )
    parser.add_argument(
        "--max-len",
        type=int,
        default=5000,
        help="Maximum clean_body character length (rows above are dropped).",
    )
    parser.add_argument(
        "--lemma-batch-size",
        type=int,
        default=256,
        help="spaCy pipe batch size for lemmatization.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    _configure_logging()
    output_dir = setup_output_dir(args.output_dir)

    logger.info("=== Stage 2: Data Cleaning & Lemmatization ===")
    logger.info("Input      : %s", args.input)
    logger.info("Output dir : %s", output_dir)
    logger.info("Body len   : [%d, %d]", args.min_len, args.max_len)

    # 1 — Load
    logger.info("Loading raw CSV …")
    df = pd.read_csv(args.input)
    logger.info("Loaded %d rows, %d columns.", len(df), len(df.columns))

    # 2 — Language filter
    df = filter_language(df, lang="en")

    # 3 — Quality checks (logging only)
    quality_checks(df)

    # 4 — Clean text
    df = apply_cleaning(df)

    # 5 — Length filter
    df = filter_body_length(df, min_len=args.min_len, max_len=args.max_len)

    # 6 — Add length columns (used in EDA)
    df = add_length_columns(df)

    # 7 — Lemmatize
    df = apply_lemmatization(df, batch_size=args.lemma_batch_size)

    # 8 — Build and save corpus
    corpus_df = build_corpus_columns(df)
    save_dataframe(corpus_df, output_dir / "cleaned_corpus.csv", label="cleaned_corpus")

    logger.info("Stage 2 complete. Rows in corpus: %d", len(corpus_df))


if __name__ == "__main__":
    main()
