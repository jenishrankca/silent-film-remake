"""Operationalizes the guide's step 8 litmus test: 'is this an instruction or a decision?'."""
from __future__ import annotations

import re
from dataclasses import dataclass

from .project import Project, Shot

VAGUE_WORDS = {"maybe", "tbd", "todo", "unclear", "probably"}
VAGUE_PATTERN = re.compile(
    r"\b(" + "|".join(re.escape(w) for w in VAGUE_WORDS) + r")\b|\?", re.IGNORECASE
)
VALID_CAMERA_MOVES = {"static", "slow push-in", "handheld", "locked-off", "dolly", "tracking"}
VALID_SHOT_TYPES = {
    "extreme close-up",
    "close-up",
    "medium",
    "wide",
    "establishing",
    "extreme wide",
}


@dataclass
class LintWarning:
    shot_id: str
    message: str


def _is_vague(text: str) -> bool:
    return not text.strip() or bool(VAGUE_PATTERN.search(text))


def lint_shot(shot: Shot) -> list[LintWarning]:
    warnings: list[LintWarning] = []

    if not shot.anchor_ref_id:
        warnings.append(LintWarning(shot.id, "no anchor reference image set"))

    if _is_vague(shot.subject_action):
        warnings.append(LintWarning(shot.id, "subject/action is empty or vague"))

    if shot.shot_type.lower() not in VALID_SHOT_TYPES:
        warnings.append(
            LintWarning(shot.id, f"shot_type '{shot.shot_type}' is not a locked instruction")
        )

    if shot.camera_move.lower() not in VALID_CAMERA_MOVES:
        warnings.append(
            LintWarning(shot.id, f"camera_move '{shot.camera_move}' is not a locked instruction")
        )

    return warnings


def lint_project(project: Project) -> list[LintWarning]:
    warnings: list[LintWarning] = []
    for shot in project.shots:
        warnings.extend(lint_shot(shot))
    return warnings
