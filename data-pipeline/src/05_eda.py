"""
05_eda.py — Stage 5: Exploratory Data Analysis & Visualisation
===============================================================

Produces all plots described in the M1 deliverables.  This script is
**completely separate from the data-processing pipeline** so it can be
skipped in headless/CI environments without affecting any output data.

All figures are saved to disk (``data/processed/*.png``); nothing is
displayed interactively.  The script uses ``matplotlib.use("Agg")``
before importing pyplot to guarantee headless compatibility.

Sections
--------
1. Queue distribution (bar chart + statistics)
2. Priority and type distributions
3. Text length distributions (body, answer)
4. Keyword analysis per queue (top-10 lemmatised terms)
5. Tag distribution and queue-tag heatmap
6. Answer quality analysis
7. Token count distribution (HuggingFace tokenizer)
8. PCA projection of body embeddings
9. Deliverables summary check

Usage
-----
    python src/05_eda.py
    python src/05_eda.py --input-csv data/processed/cleaned_corpus.csv \\
                         --input-emb data/processed/body_embeddings.npy \\
                         --output-dir data/processed \\
                         --seed 42

Outputs (all PNG files under ``data/processed/``)
-------
    queue_distribution.png
    priority_type_distribution.png
    text_length_distribution.png
    tag_distribution.png
    queue_tag_heatmap.png
    token_count_distribution.png
    embeddings_pca.png
"""

from __future__ import annotations

# Must be set before any pyplot import to ensure headless / server compatibility
import matplotlib
matplotlib.use("Agg")

import argparse
import logging
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy.stats import entropy as scipy_entropy

LOG_FMT = "%(asctime)s [%(levelname)s] %(name)s — %(message)s"
DATE_FMT = "%Y-%m-%d %H:%M:%S"
logger = logging.getLogger(__name__)

sns.set_theme(style="whitegrid")


def _configure_logging() -> None:
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    handlers: list[logging.Handler] = [
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(log_dir / "05_eda.log", encoding="utf-8"),
    ]
    logging.basicConfig(level=logging.INFO, format=LOG_FMT, datefmt=DATE_FMT,
                        handlers=handlers)


# ---------------------------------------------------------------------------
# 1. Queue distribution
# ---------------------------------------------------------------------------

def plot_queue_distribution(df: pd.DataFrame, output_dir: Path) -> None:
    """Bar chart of ticket counts per queue with imbalance statistics.

    Parameters
    ----------
    df:
        Cleaned corpus DataFrame containing a ``queue`` column.
    output_dir:
        Directory where the PNG will be saved.
    """
    queue_counts = df["queue"].value_counts()

    n_classes = len(queue_counts)
    imbalance_ratio = queue_counts.max() / queue_counts.min()
    cls_entropy = scipy_entropy(queue_counts.values)

    logger.info("Queue distribution — %d classes", n_classes)
    logger.info("Imbalance ratio (max/min): %.2f", imbalance_ratio)
    logger.info("Class entropy: %.4f", cls_entropy)
    logger.info("Queue counts:\n%s", queue_counts.to_string())

    plt.figure(figsize=(12, 6))
    queue_counts.plot(kind="bar", color=sns.color_palette("viridis", len(queue_counts)))
    plt.title(f"Queue Distribution  (n={len(df):,}  |  {n_classes} classes)", fontsize=14)
    plt.xlabel("Queue")
    plt.ylabel("Ticket Count")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    out = output_dir / "queue_distribution.png"
    plt.savefig(out, dpi=100)
    plt.close()
    logger.info("Saved: %s", out)


# ---------------------------------------------------------------------------
# 2. Priority and type distributions
# ---------------------------------------------------------------------------

def plot_priority_type(df: pd.DataFrame, output_dir: Path) -> None:
    """Side-by-side bar charts for priority and ticket type.

    Parameters
    ----------
    df:
        Cleaned corpus DataFrame.
    output_dir:
        Directory where the PNG will be saved.
    """
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    if "priority" in df.columns:
        df["priority"].value_counts().plot(
            kind="bar", ax=axes[0], color="steelblue", edgecolor="white"
        )
        axes[0].set_title("Priority Distribution")
        axes[0].set_xlabel("Priority")
        axes[0].set_ylabel("Count")
        axes[0].tick_params(axis="x", rotation=30)
    else:
        axes[0].set_visible(False)

    if "type" in df.columns:
        df["type"].value_counts().plot(
            kind="bar", ax=axes[1], color="coral", edgecolor="white"
        )
        axes[1].set_title("Ticket Type Distribution")
        axes[1].set_xlabel("Type")
        axes[1].set_ylabel("Count")
        axes[1].tick_params(axis="x", rotation=30)
    else:
        axes[1].set_visible(False)

    plt.tight_layout()
    out = output_dir / "priority_type_distribution.png"
    plt.savefig(out, dpi=100)
    plt.close()
    logger.info("Saved: %s", out)


# ---------------------------------------------------------------------------
# 3. Text length distributions
# ---------------------------------------------------------------------------

def plot_text_lengths(df: pd.DataFrame, output_dir: Path) -> None:
    """Overlapping histograms of ``body_length`` and ``answer_length``.

    Parameters
    ----------
    df:
        Cleaned corpus DataFrame.  ``body_length`` and ``answer_length``
        columns are computed on the fly if absent.
    output_dir:
        Directory where the PNG will be saved.
    """
    if "body_length" not in df.columns:
        df = df.copy()
        df["body_length"] = df["body"].str.len()
    if "answer_length" not in df.columns and "answer" in df.columns:
        df["answer_length"] = df["answer"].str.len()

    logger.info("Body length stats:\n%s", df["body_length"].describe().round(1).to_string())
    if "answer_length" in df.columns:
        logger.info(
            "Answer length stats:\n%s",
            df["answer_length"].describe().round(1).to_string(),
        )

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    axes[0].hist(
        df["body_length"].clip(upper=2000), bins=60,
        color="steelblue", edgecolor="white",
    )
    axes[0].set_title("Body Length Distribution (chars, clipped at 2000)")
    axes[0].set_xlabel("Characters")
    axes[0].set_ylabel("Frequency")

    if "answer_length" in df.columns:
        axes[1].hist(
            df["answer_length"].clip(upper=3000), bins=60,
            color="mediumseagreen", edgecolor="white",
        )
        axes[1].set_title("Answer Length Distribution (chars, clipped at 3000)")
        axes[1].set_xlabel("Characters")
        axes[1].set_ylabel("Frequency")
    else:
        axes[1].set_visible(False)

    plt.tight_layout()
    out = output_dir / "text_length_distribution.png"
    plt.savefig(out, dpi=100)
    plt.close()
    logger.info("Saved: %s", out)


# ---------------------------------------------------------------------------
# 4. Keyword analysis per queue
# ---------------------------------------------------------------------------

def log_top_keywords(df: pd.DataFrame, top_n: int = 10) -> None:
    """Log top *top_n* lemmatised keywords per queue (no plot).

    Parameters
    ----------
    df:
        Cleaned corpus DataFrame with a ``lemmatized_body`` column.
    top_n:
        Number of top keywords to log per queue.
    """
    if "lemmatized_body" not in df.columns:
        logger.warning("'lemmatized_body' column not found — skipping keyword analysis.")
        return

    logger.info("Top %d keywords per queue:", top_n)
    for queue in sorted(df["queue"].unique()):
        corpus = " ".join(df.loc[df["queue"] == queue, "lemmatized_body"].dropna())
        words = corpus.split()
        top = Counter(words).most_common(top_n)
        kw_str = ", ".join(f"{w}({c})" for w, c in top)
        logger.info("  %-30s %s", queue + ":", kw_str)


# ---------------------------------------------------------------------------
# 5. Tag distribution and queue-tag heatmap
# ---------------------------------------------------------------------------

def plot_tag_analysis(df: pd.DataFrame, output_dir: Path) -> None:
    """Bar chart of top-20 tags and a queue-tag cross-heatmap.

    Parameters
    ----------
    df:
        Cleaned corpus DataFrame.
    output_dir:
        Directory where the PNGs will be saved.
    """
    tag_cols = [c for c in df.columns if c.startswith("tag_")]
    if not tag_cols:
        logger.warning("No tag columns found — skipping tag analysis.")
        return

    all_tags = pd.concat([df[c] for c in tag_cols]).dropna()
    tag_counts = all_tags.value_counts()

    logger.info("Total unique tags: %d", len(tag_counts))
    logger.info("Top 20 tags:\n%s", tag_counts.head(20).to_string())

    # Bar chart
    plt.figure(figsize=(12, 5))
    tag_counts.head(20).plot(kind="bar", color="orchid", edgecolor="white")
    plt.title("Top 20 Tags (all tag columns combined)")
    plt.xlabel("Tag")
    plt.ylabel("Count")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    out = output_dir / "tag_distribution.png"
    plt.savefig(out, dpi=100)
    plt.close()
    logger.info("Saved: %s", out)

    # Heatmap
    top_tags = tag_counts.head(10).index.tolist()
    if "tag_1" in df.columns and "queue" in df.columns:
        cross = pd.crosstab(
            df["queue"],
            df["tag_1"].where(df["tag_1"].isin(top_tags), other="other"),
        )
        plt.figure(figsize=(14, 7))
        sns.heatmap(cross, annot=True, fmt="d", cmap="Blues", linewidths=0.4)
        plt.title("Queue vs Top-10 Primary Tags")
        plt.tight_layout()
        out = output_dir / "queue_tag_heatmap.png"
        plt.savefig(out, dpi=100)
        plt.close()
        logger.info("Saved: %s", out)


# ---------------------------------------------------------------------------
# 6. Answer quality analysis
# ---------------------------------------------------------------------------

def log_answer_quality(df: pd.DataFrame) -> None:
    """Log answer length stats, empty-answer count, and template detection.

    Parameters
    ----------
    df:
        Cleaned corpus DataFrame.
    """
    if "clean_answer" not in df.columns:
        logger.warning("'clean_answer' column not found — skipping answer quality analysis.")
        return

    if "clean_answer_length" not in df.columns:
        df = df.copy()
        df["clean_answer_length"] = df["clean_answer"].str.len()

    logger.info(
        "Clean answer length stats:\n%s",
        df["clean_answer_length"].describe().round(1).to_string(),
    )

    empty = (df["clean_answer"].str.strip() == "").sum()
    logger.info("Empty answers after cleaning: %d", empty)

    answer_vc = df["clean_answer"].value_counts()
    template_count = (answer_vc > 5).sum()
    logger.info("Unique answers:                          %d", len(answer_vc))
    logger.info("Answers appearing > 5 times (templates): %d", template_count)
    logger.info(
        "Template share:                          %.1f%%",
        template_count / len(answer_vc) * 100,
    )

    logger.info("Top 3 most repeated answers:")
    for ans, cnt in answer_vc.head(3).items():
        logger.info("  [%dx] %s …", cnt, str(ans)[:100])


# ---------------------------------------------------------------------------
# 7. Token count distribution
# ---------------------------------------------------------------------------

def plot_token_counts(
    df: pd.DataFrame,
    output_dir: Path,
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
    sample_n: int = 5000,
    seed: int = 42,
) -> None:
    """Histogram of HuggingFace tokenizer token counts for ``clean_body``.

    Parameters
    ----------
    df:
        Cleaned corpus DataFrame.
    output_dir:
        Directory where the PNG will be saved.
    model_name:
        HuggingFace tokenizer identifier to use for token counting.
    sample_n:
        Maximum number of rows to sample (for speed).
    seed:
        Random seed for the sample.
    """
    from transformers import AutoTokenizer  # deferred import

    tokenizer = AutoTokenizer.from_pretrained(model_name)

    sample_df = df.sample(min(sample_n, len(df)), random_state=seed)
    token_counts = sample_df["clean_body"].apply(
        lambda x: len(tokenizer.encode(x, add_special_tokens=True, truncation=False))
    )

    logger.info(
        "Token count distribution (sample n=%d):\n%s",
        len(sample_df),
        token_counts.describe().round(1).to_string(),
    )

    over_limit = (token_counts > 512).sum()
    pct = over_limit / len(sample_df)
    logger.info(
        "Tickets > 512 tokens (will be truncated): %d  (%.1f%%)",
        over_limit, pct * 100,
    )
    if pct > 0.10:
        logger.warning(
            "Notable truncation (%.1f%%) — consider mean-pooling on chunks in M2.",
            pct * 100,
        )
    else:
        logger.info("Truncation is minimal — standard encoding is fine.")

    plt.figure(figsize=(10, 5))
    token_counts.clip(upper=600).hist(bins=50, color="steelblue", edgecolor="white")
    plt.axvline(512, color="red", linestyle="--", linewidth=1.5, label="512-token limit")
    plt.title(f"Token Count Distribution  (clean_body, n={len(sample_df):,})")
    plt.xlabel("Token Count")
    plt.ylabel("Frequency")
    plt.legend()
    plt.tight_layout()
    out = output_dir / "token_count_distribution.png"
    plt.savefig(out, dpi=100)
    plt.close()
    logger.info("Saved: %s", out)


# ---------------------------------------------------------------------------
# 8. PCA projection of embeddings
# ---------------------------------------------------------------------------

def plot_embeddings_pca(
    df: pd.DataFrame,
    embeddings: np.ndarray,
    output_dir: Path,
    viz_n: int = 3000,
    seed: int = 42,
) -> None:
    """2-D PCA scatter plot of body embeddings, coloured by queue.

    Parameters
    ----------
    df:
        Cleaned corpus DataFrame.  Must be row-aligned with *embeddings*.
    embeddings:
        Full-corpus embedding matrix, shape ``(N, D)``.
    output_dir:
        Directory where the PNG will be saved.
    viz_n:
        Maximum number of points to plot (randomly sampled for speed).
    seed:
        Random seed for the sample.
    """
    from sklearn.decomposition import PCA  # deferred import

    rng = np.random.default_rng(seed)
    n = min(viz_n, len(df))
    idx = rng.choice(len(df), n, replace=False)

    pca = PCA(n_components=2, random_state=seed)
    coords = pca.fit_transform(embeddings[idx])
    viz_labels = df["queue"].iloc[idx].values

    queues = df["queue"].unique()
    palette = sns.color_palette("tab10", len(queues))

    plt.figure(figsize=(12, 8))
    for q, color in zip(queues, palette):
        mask = viz_labels == q
        plt.scatter(
            coords[mask, 0], coords[mask, 1],
            label=q, alpha=0.45, s=8, color=color,
        )

    plt.title(f"PCA of Ticket Embeddings  (n={n:,})")
    plt.xlabel(f"PC1  ({pca.explained_variance_ratio_[0]:.1%} var)")
    plt.ylabel(f"PC2  ({pca.explained_variance_ratio_[1]:.1%} var)")
    plt.legend(bbox_to_anchor=(1.02, 1), loc="upper left", fontsize=8, markerscale=3)
    plt.tight_layout()
    out = output_dir / "embeddings_pca.png"
    plt.savefig(out, dpi=100, bbox_inches="tight")
    plt.close()
    logger.info("Saved: %s", out)


# ---------------------------------------------------------------------------
# 9. Deliverables summary check
# ---------------------------------------------------------------------------

def print_deliverables_summary(output_dir: Path) -> None:
    """Log a summary table of all expected M1 output files.

    Parameters
    ----------
    output_dir:
        Directory where deliverables should reside.
    """
    deliverables = [
        ("cleaned_corpus.csv",              "Full cleaned corpus"),
        ("train.csv",                       "Train split  (70%)"),
        ("val.csv",                         "Validation split  (15%)"),
        ("test.csv",                        "Test split  (15%)"),
        ("body_embeddings.npy",             "Full embeddings  (384-dim)"),
        ("train_embeddings.npy",            "Train embeddings"),
        ("val_embeddings.npy",              "Val embeddings"),
        ("test_embeddings.npy",             "Test embeddings"),
        ("queue_distribution.png",          "Queue distribution plot"),
        ("priority_type_distribution.png",  "Priority/type plot"),
        ("text_length_distribution.png",    "Text length plot"),
        ("tag_distribution.png",            "Tag distribution plot"),
        ("queue_tag_heatmap.png",           "Queue-tag heatmap"),
        ("token_count_distribution.png",    "Token count plot"),
        ("embeddings_pca.png",              "Embeddings PCA plot"),
    ]

    logger.info("=" * 65)
    logger.info("  MILESTONE 1 DELIVERABLES")
    logger.info("=" * 65)

    all_ok = True
    for filename, desc in deliverables:
        path = output_dir / filename
        exists = path.exists()
        if not exists:
            all_ok = False
        mark = "OK     " if exists else "MISSING"
        size = f"{path.stat().st_size / 1024:.0f} KB" if exists else "—"
        logger.info(
            "  [%s]  %-40s %8s   %s",
            mark, desc, size, path,
        )

    logger.info("=" * 65)
    if all_ok:
        logger.info("All deliverables present. ✓")
    else:
        logger.warning("Some deliverables are missing — check the log above.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Stage 5 — EDA: generate all visualisation plots.",
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
        help="Directory to write plot PNGs into.",
    )
    parser.add_argument(
        "--tokenizer-model",
        default="sentence-transformers/all-MiniLM-L6-v2",
        help="HuggingFace tokenizer for token count analysis.",
    )
    parser.add_argument(
        "--pca-sample",
        type=int,
        default=3000,
        help="Number of points to sample for the PCA plot.",
    )
    parser.add_argument(
        "--token-sample",
        type=int,
        default=5000,
        help="Number of rows to sample for token count analysis.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for sampling.",
    )
    parser.add_argument(
        "--skip-tokenizer",
        action="store_true",
        help="Skip token count analysis (avoids HuggingFace download in offline envs).",
    )
    parser.add_argument(
        "--skip-pca",
        action="store_true",
        help="Skip PCA plot (useful when embeddings are unavailable).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    _configure_logging()

    from src.utils.io_utils import setup_output_dir
    output_dir = setup_output_dir(args.output_dir)

    logger.info("=== Stage 5: EDA & Visualisation ===")
    logger.info("Input CSV  : %s", args.input_csv)
    logger.info("Input emb  : %s", args.input_emb)
    logger.info("Output dir : %s", output_dir)

    # Load corpus
    logger.info("Loading corpus …")
    df = pd.read_csv(args.input_csv)
    logger.info("Corpus loaded — %d rows.", len(df))

    # --- Plots & analysis ---
    plot_queue_distribution(df, output_dir)
    plot_priority_type(df, output_dir)
    plot_text_lengths(df, output_dir)
    log_top_keywords(df)
    plot_tag_analysis(df, output_dir)
    log_answer_quality(df)

    if not args.skip_tokenizer:
        plot_token_counts(
            df, output_dir,
            model_name=args.tokenizer_model,
            sample_n=args.token_sample,
            seed=args.seed,
        )
    else:
        logger.info("Skipping token count analysis (--skip-tokenizer).")

    if not args.skip_pca:
        emb_path = Path(args.input_emb)
        if emb_path.exists():
            logger.info("Loading embeddings for PCA …")
            embeddings = np.load(emb_path)
            plot_embeddings_pca(df, embeddings, output_dir,
                                viz_n=args.pca_sample, seed=args.seed)
        else:
            logger.warning(
                "Embedding file not found (%s) — skipping PCA plot. "
                "Run 03_embed_data.py first.",
                emb_path,
            )
    else:
        logger.info("Skipping PCA plot (--skip-pca).")

    print_deliverables_summary(output_dir)
    logger.info("Stage 5 complete.")


if __name__ == "__main__":
    main()
