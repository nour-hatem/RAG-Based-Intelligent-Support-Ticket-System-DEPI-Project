"""
01_load_data.py — Stage 1: Dataset Download
============================================

Downloads the customer-support-tickets dataset from HuggingFace and saves
it as a raw CSV for downstream processing.  Re-running this script simply
overwrites the existing raw.csv, so it is safe to use as a cache-buster.

Usage
-----
    python src/01_load_data.py
    python src/01_load_data.py --dataset Tobi-Bueck/customer-support-tickets \\
                               --output-dir data/processed

Outputs
-------
    data/processed/raw.csv
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Allow running as  `python src/01_load_data.py`  from the repo root
# ---------------------------------------------------------------------------
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.io_utils import save_dataframe, setup_output_dir

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
LOG_FMT = "%(asctime)s [%(levelname)s] %(name)s — %(message)s"
DATE_FMT = "%Y-%m-%d %H:%M:%S"


def _configure_logging(output_dir: Path) -> None:
    """Set up console + rotating file logging."""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    handlers: list[logging.Handler] = [
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(log_dir / "01_load_data.log", encoding="utf-8"),
    ]
    logging.basicConfig(level=logging.INFO, format=LOG_FMT, datefmt=DATE_FMT,
                        handlers=handlers)


logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------

def load_and_save(dataset_name: str, output_dir: Path) -> Path:
    """Download *dataset_name* from HuggingFace and persist the train split.

    Parameters
    ----------
    dataset_name:
        HuggingFace dataset identifier, e.g.
        ``"Tobi-Bueck/customer-support-tickets"``.
    output_dir:
        Directory where ``raw.csv`` will be written.

    Returns
    -------
    Path
        Absolute path to the saved CSV file.
    """
    from datasets import load_dataset  # deferred: only needed here

    logger.info("Downloading dataset: %s", dataset_name)
    dataset = load_dataset(dataset_name)

    splits = list(dataset.keys())
    logger.info("Available splits: %s — using 'train'", splits)

    df = dataset["train"].to_pandas()
    logger.info("Raw shape: %s", df.shape)
    logger.info("Columns: %s", list(df.columns))
    logger.info("Dtypes:\n%s", df.dtypes.to_string())

    # Basic sanity info
    for col in ["language", "queue", "priority"]:
        if col in df.columns:
            vc = df[col].value_counts()
            logger.info("Value counts — '%s':\n%s", col, vc.to_string())

    out_path = output_dir / "raw.csv"
    save_dataframe(df, out_path, label="raw dataset")
    return out_path


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Stage 1 — Download dataset from HuggingFace and save raw CSV.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--dataset",
        default="Tobi-Bueck/customer-support-tickets",
        help="HuggingFace dataset name.",
    )
    parser.add_argument(
        "--output-dir",
        default="data/processed",
        help="Directory to write raw.csv into.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_dir = setup_output_dir(args.output_dir)
    _configure_logging(output_dir)

    logger.info("=== Stage 1: Data Loading ===")
    logger.info("Dataset : %s", args.dataset)
    logger.info("Output  : %s", output_dir)

    out_path = load_and_save(args.dataset, output_dir)
    logger.info("Stage 1 complete. Output: %s", out_path)


if __name__ == "__main__":
    main()
