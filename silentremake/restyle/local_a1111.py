"""Restyle via a locally-run Automatic1111 Stable Diffusion WebUI (img2img HTTP API).

Point LOCAL_SD_URL at your running instance (default: http://127.0.0.1:7860). Requires
`--api` to be enabled on the A1111 launch flags. ComfyUI is not implemented here since its
API is a bespoke per-workflow node graph rather than a stable single endpoint.
"""
from __future__ import annotations

import base64
import os
from pathlib import Path

import requests

from .base import RestyleProvider, RestyleResult

DEFAULT_URL = "http://127.0.0.1:7860"


class LocalRestyler(RestyleProvider):
    name = "local"

    def __init__(self, base_url: str | None = None, denoising_strength: float = 0.55):
        self.base_url = base_url or os.environ.get("LOCAL_SD_URL", DEFAULT_URL)
        self.denoising_strength = denoising_strength

    def restyle(self, image_path: Path, style_prompt: str, dest_path: Path) -> RestyleResult:
        image_b64 = base64.b64encode(image_path.read_bytes()).decode("ascii")
        payload = {
            "init_images": [image_b64],
            "prompt": style_prompt,
            "denoising_strength": self.denoising_strength,
        }
        try:
            resp = requests.post(
                f"{self.base_url}/sdapi/v1/img2img", json=payload, timeout=120
            )
            resp.raise_for_status()
        except requests.RequestException as e:
            return RestyleResult(
                output_path=dest_path,
                provider=self.name,
                status="pending_manual",
                message=(
                    f"Could not reach local Stable Diffusion WebUI at {self.base_url} ({e}). "
                    "Start it with the --api flag, or set LOCAL_SD_URL."
                ),
            )

        data = resp.json()
        images = data.get("images", [])
        if not images:
            return RestyleResult(
                output_path=dest_path,
                provider=self.name,
                status="pending_manual",
                message="Local SD WebUI returned no images.",
            )

        dest_path.parent.mkdir(parents=True, exist_ok=True)
        dest_path.write_bytes(base64.b64decode(images[0]))

        return RestyleResult(
            output_path=dest_path, provider=self.name, status="completed",
            message=f"Restyled via local A1111 at {self.base_url}.",
        )
