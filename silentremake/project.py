"""Project data model: the single project.yaml source of truth."""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

import yaml

SCHEMA_VERSION = 1


@dataclass
class StyleBible:
    project_name: str
    style_phrase: str
    lighting_phrase: str
    grain_grade_phrase: str
    genre_mode: str = "drama"  # "drama" | "comedy"
    default_restyle_provider: str = "manual"


@dataclass
class CandidateFrame:
    path: str
    timestamp_s: float
    frame_number: int
    sharpness: float


@dataclass
class DetectedScene:
    scene_index: int
    start_s: float
    end_s: float
    candidates: list[CandidateFrame] = field(default_factory=list)
    reviewed: bool = False
    kept: bool = False
    chosen_frame_path: Optional[str] = None


@dataclass
class ReferenceImage:
    ref_id: str
    tag: str  # "character" | "set" | "prop"
    description: str
    raw_frame_path: str
    styled_frame_path: Optional[str] = None
    restyle_status: str = "pending"  # pending | pending_manual | completed
    restyle_provider: Optional[str] = None


@dataclass
class Shot:
    id: str
    order: int
    label: str
    raw_frame_path: str
    scene_index: Optional[int] = None
    anchor_ref_id: Optional[str] = None
    shot_type: str = ""
    camera_move: str = ""
    subject_action: str = ""
    character_count: int = 1
    beat_before_gag: str = ""
    notes: str = ""
    status: str = "detected"  # detected | kept | anchored | prompted


@dataclass
class Project:
    schema_version: int
    slug: str
    style: StyleBible
    source_video_path: str
    scenes: list[DetectedScene] = field(default_factory=list)
    reference_images: list[ReferenceImage] = field(default_factory=list)
    shots: list[Shot] = field(default_factory=list)

    # -- paths -----------------------------------------------------------
    @staticmethod
    def project_dir(root: Path, slug: str) -> Path:
        return root / "projects" / slug

    @staticmethod
    def yaml_path(root: Path, slug: str) -> Path:
        return Project.project_dir(root, slug) / "project.yaml"

    # -- persistence -------------------------------------------------------
    def save(self, root: Path) -> None:
        path = self.yaml_path(root, self.slug)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            yaml.safe_dump(asdict(self), f, sort_keys=False, allow_unicode=True)

    @staticmethod
    def load(root: Path, slug: str) -> "Project":
        path = Project.yaml_path(root, slug)
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return Project._from_dict(data)

    @staticmethod
    def _from_dict(data: dict) -> "Project":
        style = StyleBible(**data["style"])
        scenes = [
            DetectedScene(
                scene_index=s["scene_index"],
                start_s=s["start_s"],
                end_s=s["end_s"],
                candidates=[CandidateFrame(**c) for c in s.get("candidates", [])],
                reviewed=s.get("reviewed", False),
                kept=s.get("kept", False),
                chosen_frame_path=s.get("chosen_frame_path"),
            )
            for s in data.get("scenes", [])
        ]
        refs = [ReferenceImage(**r) for r in data.get("reference_images", [])]
        shots = [Shot(**sh) for sh in data.get("shots", [])]
        return Project(
            schema_version=data.get("schema_version", SCHEMA_VERSION),
            slug=data["slug"],
            style=style,
            source_video_path=data["source_video_path"],
            scenes=scenes,
            reference_images=refs,
            shots=shots,
        )

    # -- helpers -----------------------------------------------------------
    def get_scene(self, scene_index: int) -> Optional[DetectedScene]:
        for s in self.scenes:
            if s.scene_index == scene_index:
                return s
        return None

    def get_ref(self, ref_id: str) -> Optional[ReferenceImage]:
        for r in self.reference_images:
            if r.ref_id == ref_id:
                return r
        return None


def slugify(text: str) -> str:
    keep = [c.lower() if c.isalnum() else "-" for c in text.strip()]
    slug = "".join(keep)
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug.strip("-") or "project"
