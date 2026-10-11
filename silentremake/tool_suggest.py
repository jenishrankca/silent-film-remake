"""Informational tool-suggestion heuristic (guide section 4) + multi-character drift warning."""
from __future__ import annotations

from .project import Shot

WIDE_SHOT_TYPES = {"wide", "establishing", "extreme wide"}


def suggest_tool(shot: Shot) -> str:
    if shot.character_count >= 2:
        return "Kling 3.0 (multi-character 'Elements' handling)"
    if shot.shot_type.lower() in WIDE_SHOT_TYPES:
        return "Veo 3 (wide/establishing realism)"
    return "Seedance 2.0 (character-lock consistency, main workhorse)"


def drift_warning(shot: Shot) -> str | None:
    if shot.character_count >= 2:
        return (
            "2+ characters interacting: expect drift at the point of contact. "
            "Plan a manual touch-up or a reaction-shot cutaway before the interaction gets complex."
        )
    return None
