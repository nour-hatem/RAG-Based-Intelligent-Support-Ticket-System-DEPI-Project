"""
split_utils.py — Stratified train/val/test split helper for the M1 data-pipeline.

Encapsulates the two-pass sklearn split so the logic is testable independently
of the pipeline scripts and can be reused in experiment sweeps.
"""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

logger = logging.getLogger(__name__)


def stratified_split(
    df: pd.DataFrame,
    embeddings: np.ndarray,
    stratify_col: str = "queue",
    val_size: float = 0.15,
    test_size: float = 0.15,
    seed: int = 42,
) -> tuple[
    pd.DataFrame, pd.DataFrame, pd.DataFrame,
    np.ndarray, np.ndarray, np.ndarray,
]:
    """Split a DataFrame and its paired embeddings into train / val / test sets.

    The split is stratified on *stratify_col* to preserve class distribution
    in all three partitions.  Embeddings are sliced **before** the DataFrame
    index is reset so row alignment is guaranteed.

    Parameters
    ----------
    df:
        Cleaned corpus DataFrame.  Must contain *stratify_col*.
    embeddings:
        Embedding matrix with shape ``(len(df), D)``.  Must be row-aligned
        with *df* (i.e. ``embeddings[i]`` corresponds to ``df.iloc[i]``).
    stratify_col:
        Column to stratify on.  Defaults to ``"queue"``.
    val_size:
        Fraction of the full dataset to reserve for validation.
        Defaults to ``0.15`` (15 %).
    test_size:
        Fraction of the full dataset to reserve for testing.
        Defaults to ``0.15`` (15 %).
    seed:
        Random seed for reproducibility.  Defaults to ``42``.

    Returns
    -------
    tuple
        ``(train_df, val_df, test_df, train_emb, val_emb, test_emb)``
        Each DataFrame has a clean, zero-based integer index.

    Raises
    ------
    ValueError
        If ``len(df) != len(embeddings)``.
    ValueError
        If *stratify_col* is not a column in *df*.
    """
    if len(df) != len(embeddings):
        raise ValueError(
            f"DataFrame length ({len(df)}) does not match embeddings length "
            f"({len(embeddings)}).  Ensure they share the same row order."
        )
    if stratify_col not in df.columns:
        raise ValueError(
            f"Stratify column '{stratify_col}' not found in DataFrame.  "
            f"Available columns: {list(df.columns)}"
        )

    combined_holdout = val_size + test_size
    # relative test fraction within the temp (holdout) split
    relative_test = test_size / combined_holdout

    logger.info(
        "Splitting %d rows — train=%.0f%%  val=%.0f%%  test=%.0f%%  "
        "stratify_col='%s'  seed=%d",
        len(df),
        (1 - combined_holdout) * 100,
        val_size * 100,
        test_size * 100,
        stratify_col,
        seed,
    )

    train_df, temp_df = train_test_split(
        df,
        test_size=combined_holdout,
        stratify=df[stratify_col],
        random_state=seed,
    )
    val_df, test_df = train_test_split(
        temp_df,
        test_size=relative_test,
        stratify=temp_df[stratify_col],
        random_state=seed,
    )

    # Slice embeddings BEFORE resetting indices so alignment is preserved
    train_emb = embeddings[train_df.index]
    val_emb   = embeddings[val_df.index]
    test_emb  = embeddings[test_df.index]

    train_df = train_df.reset_index(drop=True)
    val_df   = val_df.reset_index(drop=True)
    test_df  = test_df.reset_index(drop=True)

    logger.info(
        "Split complete — train=%d  val=%d  test=%d",
        len(train_df), len(val_df), len(test_df),
    )

    # Log per-class proportions for a quick sanity check
    cmp = pd.DataFrame(
        {
            "train": train_df[stratify_col].value_counts(normalize=True),
            "val":   val_df[stratify_col].value_counts(normalize=True),
            "test":  test_df[stratify_col].value_counts(normalize=True),
        }
    ).round(3)
    logger.info("Queue proportions per split:\n%s", cmp.to_string())

    return train_df, val_df, test_df, train_emb, val_emb, test_emb
