"""
io_utils.py — Shared I/O helpers for the M1 data-pipeline.

Provides thin wrappers around pandas / numpy save operations so all
scripts log consistently and output paths are created automatically.
"""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def setup_output_dir(path: str | Path) -> Path:
    """Create *path* (and any parents) if it does not exist.

    Parameters
    ----------
    path:
        Directory to create.

    Returns
    -------
    Path
        Resolved :class:`pathlib.Path` for the created directory.
    """
    out = Path(path)
    out.mkdir(parents=True, exist_ok=True)
    logger.debug("Output directory ready: %s", out.resolve())
    return out


def save_dataframe(df: pd.DataFrame, path: Path, label: str = "") -> None:
    """Save *df* to a CSV at *path*, logging the shape and size.

    Parameters
    ----------
    df:
        DataFrame to persist.
    path:
        Destination file path (including filename).
    label:
        Human-readable name used in log messages (e.g. ``"cleaned_corpus"``).
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    size_kb = path.stat().st_size / 1024
    logger.info(
        "Saved %s → %s  shape=%s  (%.0f KB)",
        label or path.name,
        path,
        df.shape,
        size_kb,
    )


def save_embeddings(arr: np.ndarray, path: Path, label: str = "") -> None:
    """Save a numpy array to *path* as a ``.npy`` file.

    Parameters
    ----------
    arr:
        Embedding matrix to save, typically shape ``(N, D)``.
    path:
        Destination file path (must end in ``.npy``).
    label:
        Human-readable name used in log messages.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    np.save(path, arr)
    size_mb = path.stat().st_size / (1024 * 1024)
    logger.info(
        "Saved %s → %s  shape=%s  dtype=%s  (%.1f MB)",
        label or path.name,
        path,
        arr.shape,
        arr.dtype,
        size_mb,
    )
