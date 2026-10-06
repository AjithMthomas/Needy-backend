"""Environment access for nuvra.

One helper, one place. Every setting has a default so the project boots
on a fresh machine or free-tier host with zero configuration.
"""

from __future__ import annotations

import os
from collections.abc import Callable
from pathlib import Path


def _load_dotenv() -> None:
    """Tiny .env loader (KEY=VALUE lines, # comments). Avoids the
    python-dotenv dependency for something this small."""
    candidates = [
        Path(__file__).resolve().parent.parent / ".env",  # backend/.env
        Path.cwd() / ".env",
    ]
    for path in candidates:
        if not path.is_file():
            continue
        try:
            for line in path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                os.environ.setdefault(key.strip(), value.strip())
        except OSError:
            continue
        break


_load_dotenv()


class Cast:
    """Explicit casting helpers for nuvra_env()."""

    @staticmethod
    def int(value: str) -> int:
        return int(value)

    @staticmethod
    def float(value: str) -> float:
        return float(value)

    @staticmethod
    def bool(value: str) -> bool:
        return value.strip().lower() in {"1", "true", "yes", "on"}

    @staticmethod
    def csv(value: str) -> list[str]:
        return [item.strip() for item in value.split(",") if item.strip()]


EnvCast = Callable[[str], int | float | bool | list[str]]


def needy_env(key: str, default: str = "", cast: EnvCast | None = None):
    """Read KEY from the environment, falling back to `default`.

    `cast` may be one of the helpers in `Cast` (int/float/bool/csv) or any
    callable taking a str. Passing None returns the raw string.
    """
    raw = os.environ.get(key, default)
    if cast is None:
        return raw
    return cast(raw)


nuvra_env = needy_env
