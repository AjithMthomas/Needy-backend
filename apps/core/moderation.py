"""Server-side content moderation — port of ``lib/core/moderation.dart``.

The Flutter app screens posts client-side for instant feedback, but the
client is never trusted: every write endpoint (posts, auctions, chat,
board ideas) re-runs this screen before persisting. Word lists live in
``settings.NUVRA`` so they can be tuned without a deploy of the clients.

The server variant is strictly stronger than the client one: it also
catches letter-spaced evasion ("w e e d") which the Dart screen misses.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from django.conf import settings

_LEET_MAP = str.maketrans({"0": "o", "1": "i", "8": "b", "5": "s", "3": "e", "4": "a"})
_NON_ALPHA = re.compile(r"[^a-z ]")
_SPACES = re.compile(r"\s+")

HARD_REASON = (
    "This post conflicts with community safety rules. Remove inappropriate wording to publish."
)
SOFT_REASON = "This wording may be misread. Please rephrase before publishing."


@dataclass(frozen=True)
class Verdict:
    blocked: bool
    reason: str = ""

    @property
    def clean(self) -> bool:
        return not self.blocked


def normalize(text: str) -> str:
    """Fold leetspeak and spacing evasions before matching (same as Dart)."""
    lowered = text.lower().translate(_LEET_MAP)
    lowered = _NON_ALPHA.sub(" ", lowered)
    return _SPACES.sub(" ", lowered).strip()


def _squash_spaces(text: str) -> str:
    """Also fold single-letter spacing: 'w e e d' -> 'weed'."""
    return re.sub(r"\b(?:\w )+\w\b", lambda m: m.group(0).replace(" ", ""), text)


def screen(title: str, description: str = "") -> Verdict:
    """Return a Verdict; clean == False means the post must not be published."""
    nuvra = settings.NUVRA
    text = normalize(f"{title} {description}")
    # Match against both the normal and the space-squashed variant so
    # letter-spaced evasion is caught too.
    squashed = _squash_spaces(text)
    for word in nuvra["MODERATION_HARD_WORDS"]:
        needle = word.strip()
        if needle in text or needle in squashed:
            return Verdict(blocked=True, reason=HARD_REASON)
    for word in nuvra["MODERATION_SOFT_WORDS"]:
        if word in text or word in squashed:
            return Verdict(blocked=True, reason=SOFT_REASON)
    return Verdict(blocked=False)
