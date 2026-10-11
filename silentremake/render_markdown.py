"""Markdown shot-list renderer — the copy-paste-ready source of truth doc."""
from __future__ import annotations

import os
from pathlib import Path

from .project import Project
from . import prompt_builder, tool_suggest, lint


def _rel(path: str, out_dir: Path) -> str:
    return os.path.relpath(path, start=out_dir).replace("\\", "/")


def render_markdown(project: Project, out_path: Path) -> None:
    out_dir = out_path.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    warnings_by_shot: dict[str, list[str]] = {}
    for w in lint.lint_project(project):
        warnings_by_shot.setdefault(w.shot_id, []).append(w.message)

    lines: list[str] = []
    style = project.style
    lines.append(f"# {style.project_name} — Shot List")
    lines.append("")
    lines.append("## Look Bible (locked — identical across every shot)")
    lines.append(f"- **Style:** {style.style_phrase}")
    lines.append(f"- **Lighting:** {style.lighting_phrase}")
    lines.append(f"- **Grain/Grade:** {style.grain_grade_phrase}")
    lines.append(f"- **Genre mode:** {style.genre_mode}")
    lines.append("")
    lines.append("## Reference Sheet")
    lines.append("")
    lines.append("| Ref ID | Tag | Description | Image | Restyle Status |")
    lines.append("|---|---|---|---|---|")
    for ref in project.reference_images:
        image = ref.styled_frame_path or ref.raw_frame_path
        lines.append(
            f"| {ref.ref_id} | {ref.tag} | {ref.description} "
            f"| ![{ref.ref_id}]({_rel(image, out_dir)}) | {ref.restyle_status} |"
        )
    lines.append("")
    lines.append("## Shots")
    lines.append("")

    for shot in sorted(project.shots, key=lambda s: s.order):
        ref = project.get_ref(shot.anchor_ref_id) if shot.anchor_ref_id else None
        image = (ref.styled_frame_path or ref.raw_frame_path) if ref else shot.raw_frame_path
        prompt = prompt_builder.build_prompt(shot, style)
        suggestion = tool_suggest.suggest_tool(shot)
        drift = tool_suggest.drift_warning(shot)

        lines.append(f"### Shot {shot.order:03d} — {shot.label}")
        lines.append(f"![{shot.id}]({_rel(image, out_dir)})")
        lines.append("")
        lines.append(f"- **Anchor:** {shot.anchor_ref_id or '(none)'}")
        lines.append(f"- **Shot type:** {shot.shot_type or '(unset)'}")
        lines.append(f"- **Camera:** {shot.camera_move or '(unset)'}")
        lines.append(f"- **Action:** {shot.subject_action or '(unset)'}")
        if style.genre_mode == "comedy" and shot.beat_before_gag:
            lines.append(f"- **Beat before gag:** {shot.beat_before_gag}")
        lines.append(f"- **Character count:** {shot.character_count}")
        lines.append(f"- **Suggested tool:** {suggestion}")
        if drift:
            lines.append(f"- ⚠️ **Drift warning:** {drift}")
        if shot.notes:
            lines.append(f"- **Notes:** {shot.notes}")
        if shot.id in warnings_by_shot:
            lines.append("")
            lines.append("> **LINT WARNINGS — not yet a locked instruction:**")
            for msg in warnings_by_shot[shot.id]:
                lines.append(f"> - {msg}")
        lines.append("")
        lines.append("**Generation prompt:**")
        lines.append("```")
        lines.append(prompt)
        lines.append("```")
        lines.append("")
        lines.append("---")
        lines.append("")

    out_path.write_text("\n".join(lines), encoding="utf-8")
