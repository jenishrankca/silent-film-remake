"""Fills the guide's fixed 5-field prompt template from a Shot + the locked StyleBible."""
from __future__ import annotations

from .project import Shot, StyleBible


def build_prompt(shot: Shot, style: StyleBible) -> str:
    """[shot type] of [subject] [action], [camera move], [lighting], [style/grain/grade]"""
    action = shot.subject_action
    if style.genre_mode == "comedy" and shot.beat_before_gag:
        action = f"{action}, {shot.beat_before_gag}"

    field1 = f"{shot.shot_type} of {action}".strip()
    field2 = shot.camera_move
    field3 = style.lighting_phrase
    field4 = f"{style.grain_grade_phrase}, {style.style_phrase}"

    return ", ".join(p for p in [field1, field2, field3, field4] if p)
