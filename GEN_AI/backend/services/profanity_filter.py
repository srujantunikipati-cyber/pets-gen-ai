"""
Lightweight profanity / abuse-word filter.

No external dependencies — uses a curated regex wordlist covering:
  - Common English profanity
  - Transliterated Indian-language abuse words (hi / mr / te / ta / kn / bn / pa / gu)

Usage::

    pf = ProfanityFilter()
    clean, was_dirty = pf.clean("what the fuck is this")
    # clean  → "what the **** is this"
    # was_dirty → True
"""

from __future__ import annotations

import logging
import re
from typing import Tuple

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Word list
# ---------------------------------------------------------------------------

# fmt: off
_RAW_WORDS: list[str] = [
    # ── English ──────────────────────────────────────────────────────────
    "fuck", "fucking", "fucked", "fucker", "fucks",
    "shit", "shitting", "shitty", "shits",
    "bitch", "bitches",
    "bastard", "bastards",
    "asshole", "assholes", "ass",
    "bullshit",
    "damn", "damnit",
    "crap",
    "piss", "pissed", "pissing",
    "cock", "cocks",
    "dick", "dicks",
    "pussy", "pussies",
    "cunt", "cunts",
    "whore", "whores",
    "slut", "sluts",
    "motherfucker", "motherfucking",
    "jackass",
    "retard", "retarded",
    "faggot", "fag",
    "nigger", "nigga",
    "idiot", "moron", "imbecile",  # borderline — sometimes OK in roast context, kept light

    # ── Transliterated Hindi / Urdu ──────────────────────────────────────
    "madarchod", "madarchod", "madar", "maderchod",
    "bhenchod", "bhen", "behenchod",
    "chutiya", "chootiya", "chutiye",
    "randi", "randwa",
    "harami", "haraami",
    "saala", "saale", "sali", "saali",
    "gaandu", "gandu",
    "bokachoda", "boka",
    "lodu", "loda",
    "mc", "bc", "bsdk", "mbc",   # common abbreviated forms

    # ── Transliterated Marathi ───────────────────────────────────────────
    "zhavadya", "zavadya",
    "aai zhav", "aaizavya",

    # ── Transliterated Telugu ────────────────────────────────────────────
    "dengu", "dengey",
    "pooku", "puku",
    "gudda", "lanjaa", "lanja",
    "nakkalodu",

    # ── Transliterated Tamil ─────────────────────────────────────────────
    "oombu", "sunni", "pundai",
    "otha", "thevdiya",

    # ── Transliterated Kannada ───────────────────────────────────────────
    "ninna amma", "lanji", "tika",
    "hengasida", "sule",

    # ── Transliterated Bengali ───────────────────────────────────────────
    "bokachoda", "choda", "chudir", "khanki",

    # ── Transliterated Punjabi ───────────────────────────────────────────
    "bhene di", "teri maa", "teri bhen",

    # ── Transliterated Gujarati ──────────────────────────────────────────
    "bhen na bhosda", "gando",
]
# fmt: on


# ---------------------------------------------------------------------------
# Compile patterns once at import time
# ---------------------------------------------------------------------------

def _build_pattern(words: list[str]) -> re.Pattern:
    """Return a case-insensitive pattern matching any word in *words*."""
    escaped = sorted(
        (re.escape(w) for w in set(words)),
        key=len,
        reverse=True,   # longest first so "motherfucker" matches before "fucker"
    )
    return re.compile(r"\b(?:" + "|".join(escaped) + r")\b", re.IGNORECASE)


_PATTERN: re.Pattern = _build_pattern(_RAW_WORDS)


# ---------------------------------------------------------------------------
# Filter class
# ---------------------------------------------------------------------------

class ProfanityFilter:
    """
    Replaces profane words with ``***``.

    Thread-safe — all state is immutable after construction.
    """

    def __init__(self, replacement: str = "***") -> None:
        self._replacement = replacement

    def clean(self, text: str) -> Tuple[str, bool]:
        """
        Sanitise *text*.

        Returns:
            (cleaned_text, was_filtered) — ``was_filtered`` is True when at
            least one word was replaced.
        """
        if not text or not text.strip():
            return text, False

        cleaned, n_subs = _PATTERN.subn(self._replacement, text)
        was_filtered = n_subs > 0
        if was_filtered:
            logger.info("ProfanityFilter: replaced %d term(s) in text.", n_subs)
        return cleaned, was_filtered

    def is_clean(self, text: str) -> bool:
        """Return True when *text* contains no profanity."""
        return not bool(_PATTERN.search(text))

    def has_profanity(self, text: str) -> bool:
        """Return True when *text* contains at least one profane term."""
        return bool(_PATTERN.search(text))


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

_filter = ProfanityFilter()


def clean_text(text: str) -> Tuple[str, bool]:
    """
    Module-level convenience wrapper around :class:`ProfanityFilter`.

    Returns ``(cleaned_text, was_filtered)``.
    """
    return _filter.clean(text)
