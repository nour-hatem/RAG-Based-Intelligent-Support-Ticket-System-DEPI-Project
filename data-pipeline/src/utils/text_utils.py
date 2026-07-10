"""
text_utils.py — Text cleaning and lemmatization helpers for the M1 data-pipeline.

All functions are stateless and importable independently of the pipeline scripts,
so they can be reused in downstream milestones (M2 inference, evaluation, etc.).
"""

from __future__ import annotations

import logging
import re
import unicodedata

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Domain-specific stop-words (supplement spaCy's built-in list)
# ---------------------------------------------------------------------------
DOMAIN_STOPS: frozenset[str] = frozenset(
    {
        "the", "a", "an", "i", "my", "to", "for", "in", "is", "was", "am",
        "not", "this", "there", "be", "with", "on", "and", "of", "you", "we",
        "our", "your", "have", "would", "could", "please", "dear", "support",
        "team", "customer", "help", "issue", "ticket", "request", "problem",
        "contact", "hi", "hello", "thank", "thanks", "use", "get", "let", "know",
    }
)


def clean_text(text: str) -> str:
    """Normalize and clean raw ticket text.

    Applies the following transformations in order:

    1. Convert to ``str`` (handles NaN / numeric values gracefully).
    2. **Unicode NFKC** normalization — collapses ligatures, replaces
       full-width characters, etc.
    3. **HTML tag** removal (``<…>``).
    4. **URL** removal (``https://…``, ``www.…``).
    5. **Email** removal (``user@domain.tld``).
    6. **Lowercase**.
    7. Strip non-alphanumeric characters (digits are intentionally kept).
    8. Collapse consecutive whitespace.

    Parameters
    ----------
    text:
        Raw ticket body or answer string.

    Returns
    -------
    str
        Cleaned text, stripped of leading/trailing whitespace.

    Examples
    --------
    >>> clean_text("<b>Hello!</b> Visit https://example.com for info.")
    'hello visit for info'
    """
    text = str(text)
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"<[^>]+>", " ", text)                        # HTML tags
    text = re.sub(r"https?://\S+|www\.\S+", " ", text)          # URLs
    text = re.sub(r"\S+@\S+\.\S+", " ", text)                   # emails
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)                    # non-alphanum
    text = re.sub(r"\s+", " ", text).strip()                    # whitespace
    return text


def lemmatize_corpus(
    texts: list[str],
    batch_size: int = 256,
    min_token_len: int = 3,
) -> dict[str, str]:
    """Lemmatize and stop-word filter a list of (unique) cleaned texts.

    Loads the ``en_core_web_sm`` spaCy model with ``parser`` and ``ner``
    disabled for speed.  Processes texts in batches via :meth:`nlp.pipe`
    to avoid loading each document individually.

    Parameters
    ----------
    texts:
        List of already-cleaned text strings to lemmatize.  Passing only
        unique texts (de-duplicated upstream) avoids redundant computation.
    batch_size:
        Number of texts processed per spaCy batch. Larger values use more
        RAM; 256 is a safe default for most machines.
    min_token_len:
        Tokens shorter than this number of characters are discarded.
        Defaults to ``3`` to remove single-letter and two-letter tokens.

    Returns
    -------
    dict[str, str]
        Mapping ``{original_clean_text: lemmatized_string}``.  Feed the
        result into :meth:`pandas.Series.map` to apply to a DataFrame column.

    Raises
    ------
    OSError
        If the ``en_core_web_sm`` model is not installed.  Run
        ``python -m spacy download en_core_web_sm`` to fix this.
    """
    import spacy  # deferred import — not required at module load time

    logger.info("Loading spaCy model en_core_web_sm …")
    nlp = spacy.load("en_core_web_sm", disable=["parser", "ner"])

    logger.info("Lemmatizing %d unique texts (batch_size=%d) …", len(texts), batch_size)
    lemma_map: dict[str, str] = {}

    for doc, text in zip(nlp.pipe(texts, batch_size=batch_size), texts):
        tokens = [
            tok.lemma_
            for tok in doc
            if not tok.is_stop
            and tok.lemma_ not in DOMAIN_STOPS
            and len(tok.text) >= min_token_len
        ]
        lemma_map[text] = " ".join(tokens)

    logger.info("Lemmatization complete — %d entries in map.", len(lemma_map))
    return lemma_map
