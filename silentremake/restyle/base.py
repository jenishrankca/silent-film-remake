"""Pluggable restyle-provider interface. Restyling runs once per curated reference image,
never per shot -- this is what keeps API-backed providers cheap."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path


@dataclass
class RestyleResult:
    output_path: Path
    provider: str
    status: str  # "completed" | "pending_manual"
    message: str = ""


class RestyleProvider(ABC):
    name: str

    @abstractmethod
    def restyle(self, image_path: Path, style_prompt: str, dest_path: Path) -> RestyleResult: ...
