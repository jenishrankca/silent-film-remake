"""Restyle via Google AI Studio's Gemini image-generation endpoint (plain REST, no SDK dep).

Requires the GEMINI_API_KEY environment variable. Never read from or written to project.yaml.
"""
from __future__ import annotations

import base64
import mimetypes
import os
from pathlib import Path

import requests

from .base import RestyleProvider, RestyleResult

DEFAULT_MODEL = "gemini-2.5-flash-image"
API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


class GeminiRestyler(RestyleProvider):
    name = "gemini"

    def __init__(self, model: str | None = None):
        self.model = model or os.environ.get("GEMINI_MODEL", DEFAULT_MODEL)

    def restyle(self, image_path: Path, style_prompt: str, dest_path: Path) -> RestyleResult:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            return RestyleResult(
                output_path=dest_path,
                provider=self.name,
                status="pending_manual",
                message="GEMINI_API_KEY is not set. Export it and re-run `restyle --provider gemini`.",
            )

        mime_type = mimetypes.guess_type(str(image_path))[0] or "image/jpeg"
        image_b64 = base64.b64encode(image_path.read_bytes()).decode("ascii")

        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": f"Restyle this frame: {style_prompt}"},
                        {"inline_data": {"mime_type": mime_type, "data": image_b64}},
                    ]
                }
            ]
        }
        url = API_URL.format(model=self.model)
        resp = None
        try:
            resp = requests.post(
                url, headers={"x-goog-api-key": api_key}, json=payload, timeout=60
            )
            resp.raise_for_status()
        except requests.RequestException as e:
            # Scrub: the key goes in a header now, not the URL, so it can't leak into
            # exception reprs/tracebacks the way a query-param key would.
            detail = f"HTTP {resp.status_code}: {resp.text[:300]}" if resp is not None else str(e)
            return RestyleResult(
                output_path=dest_path,
                provider=self.name,
                status="pending_manual",
                message=f"Gemini request failed: {detail}",
            )
        data = resp.json()

        parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
        image_part = next((p for p in parts if "inline_data" in p or "inlineData" in p), None)
        if image_part is None:
            return RestyleResult(
                output_path=dest_path,
                provider=self.name,
                status="pending_manual",
                message="Gemini response did not contain an image; check the API response/model name.",
            )

        inline = image_part.get("inline_data") or image_part.get("inlineData")
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        dest_path.write_bytes(base64.b64decode(inline["data"]))

        return RestyleResult(
            output_path=dest_path, provider=self.name, status="completed",
            message=f"Restyled via {self.model}.",
        )
