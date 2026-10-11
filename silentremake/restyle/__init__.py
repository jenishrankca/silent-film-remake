from __future__ import annotations

from .base import RestyleProvider, RestyleResult
from .manual import ManualRestyler
from .gemini import GeminiRestyler
from .local_a1111 import LocalRestyler

_PROVIDERS = {
    "manual": ManualRestyler,
    "gemini": GeminiRestyler,
    "local": LocalRestyler,
}


def get_provider(name: str) -> RestyleProvider:
    try:
        return _PROVIDERS[name]()
    except KeyError:
        raise ValueError(f"Unknown restyle provider '{name}'. Choices: {', '.join(_PROVIDERS)}")


__all__ = ["RestyleProvider", "RestyleResult", "get_provider"]
