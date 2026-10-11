"""Default provider: no API call. Copies the raw frame + writes a prompt sidecar for you to
paste into any web UI (Leonardo.ai, Bing Image Creator, etc.), matching the guide's step 2."""
from __future__ import annotations

import hashlib
import shutil
from pathlib import Path

from .base import RestyleProvider, RestyleResult


def _hash_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class ManualRestyler(RestyleProvider):
    name = "manual"

    def restyle(self, image_path: Path, style_prompt: str, dest_path: Path) -> RestyleResult:
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(image_path, dest_path)

        sidecar = dest_path.with_suffix(dest_path.suffix + ".prompt.txt")
        sidecar.write_text(style_prompt, encoding="utf-8")

        hash_sidecar = dest_path.with_suffix(dest_path.suffix + ".orighash.txt")
        hash_sidecar.write_text(_hash_file(dest_path), encoding="utf-8")

        return RestyleResult(
            output_path=dest_path,
            provider=self.name,
            status="pending_manual",
            message=(
                f"Paste the prompt in {sidecar} into your image tool of choice, "
                f"then overwrite {dest_path} with the result and run `restyle --check`."
            ),
        )

    def check(self, dest_path: Path) -> bool:
        """Returns True if the file at dest_path has been overwritten since restyle() ran."""
        hash_sidecar = dest_path.with_suffix(dest_path.suffix + ".orighash.txt")
        if not dest_path.exists() or not hash_sidecar.exists():
            return False
        original_hash = hash_sidecar.read_text(encoding="utf-8").strip()
        return _hash_file(dest_path) != original_hash
