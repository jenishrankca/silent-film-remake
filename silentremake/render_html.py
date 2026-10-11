"""Static HTML grid renderer, shared by the review overview page and the final storyboard."""
from __future__ import annotations

import html
import os
from dataclasses import dataclass, field
from pathlib import Path

from .project import Project
from . import prompt_builder, tool_suggest, lint

CSS = """
body { font-family: system-ui, sans-serif; background: #16161a; color: #eaeaea; margin: 0; padding: 24px; }
h1 { font-weight: 600; }
.meta { color: #9a9aa5; margin-bottom: 24px; }
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 20px; }
.card { background: #202024; border-radius: 8px; overflow: hidden; border: 1px solid #2e2e33; }
.card img { width: 100%; display: block; background: #000; aspect-ratio: 4/3; object-fit: cover; }
.card .body { padding: 12px 14px; }
.card h3 { margin: 0 0 6px 0; font-size: 15px; }
.card p { margin: 4px 0; font-size: 13px; color: #c4c4cc; }
.card pre { background: #101012; padding: 8px; border-radius: 4px; font-size: 12px;
            white-space: pre-wrap; word-break: break-word; }
.warn { color: #f0a35a; font-size: 12px; }
"""


@dataclass
class Card:
    image_path: str
    heading: str
    body_lines: list[str] = field(default_factory=list)
    prompt: str | None = None
    warning: str | None = None


def render_grid(title: str, subtitle: str, cards: list[Card], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    parts = [
        "<!doctype html><html><head><meta charset='utf-8'>",
        f"<title>{html.escape(title)}</title><style>{CSS}</style></head><body>",
        f"<h1>{html.escape(title)}</h1><p class='meta'>{html.escape(subtitle)}</p>",
        "<div class='grid'>",
    ]
    for card in cards:
        rel_image = os.path.relpath(card.image_path, start=out_path.parent)
        rel_image = rel_image.replace("\\", "/")
        parts.append("<div class='card'>")
        parts.append(f"<img src='{html.escape(rel_image)}' alt=''>")
        parts.append("<div class='body'>")
        parts.append(f"<h3>{html.escape(card.heading)}</h3>")
        for line in card.body_lines:
            parts.append(f"<p>{html.escape(line)}</p>")
        if card.prompt:
            parts.append(f"<pre>{html.escape(card.prompt)}</pre>")
        if card.warning:
            parts.append(f"<p class='warn'>{html.escape(card.warning)}</p>")
        parts.append("</div></div>")
    parts.append("</div></body></html>")

    out_path.write_text("\n".join(parts), encoding="utf-8")


def render_storyboard(project: Project, out_path: Path) -> None:
    warnings_by_shot = {w.shot_id: w for w in lint.lint_project(project)}
    cards: list[Card] = []
    for shot in sorted(project.shots, key=lambda s: s.order):
        ref = project.get_ref(shot.anchor_ref_id) if shot.anchor_ref_id else None
        image_path = (ref.styled_frame_path or ref.raw_frame_path) if ref else shot.raw_frame_path
        prompt = prompt_builder.build_prompt(shot, project.style)
        body = [
            f"Shot type: {shot.shot_type or '(unset)'}",
            f"Camera: {shot.camera_move or '(unset)'}",
            f"Anchor: {shot.anchor_ref_id or '(none)'}",
            f"Suggested tool: {tool_suggest.suggest_tool(shot)}",
        ]
        warning = tool_suggest.drift_warning(shot)
        if shot.id in warnings_by_shot:
            body.append("LINT: needs attention before generation")
        cards.append(
            Card(
                image_path=image_path,
                heading=f"{shot.order:03d} — {shot.label}",
                body_lines=body,
                prompt=prompt,
                warning=warning,
            )
        )
    render_grid(
        title=f"{project.style.project_name} — Storyboard",
        subtitle=f"style: {project.style.style_phrase} | lighting: {project.style.lighting_phrase}",
        cards=cards,
        out_path=out_path,
    )
