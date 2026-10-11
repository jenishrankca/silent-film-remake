"""CLI entry point: python -m silentremake <command> <slug> [options]"""
from __future__ import annotations

import argparse
from pathlib import Path

from .project import Project, StyleBible, SCHEMA_VERSION
from . import detect, review, shots as shots_module, lint, render_markdown, render_html
from .restyle import get_provider
from .envfile import load_dotenv


def cmd_init(args: argparse.Namespace) -> None:
    root = Path.cwd()
    slug = args.slug

    if Project.yaml_path(root, slug).exists():
        print(f"Project '{slug}' already exists at {Project.project_dir(root, slug)}")
        return

    source = Path(args.source)
    if not source.exists():
        print(f"Source video not found: {source}")
        return

    style = StyleBible(
        project_name=args.name or slug,
        style_phrase=args.style,
        lighting_phrase=args.lighting,
        grain_grade_phrase=args.grade,
        genre_mode=args.genre,
        default_restyle_provider=args.provider,
    )
    project = Project(
        schema_version=SCHEMA_VERSION,
        slug=slug,
        style=style,
        source_video_path=str(source.resolve()),
    )
    project.save(root)
    print(f"Created project '{slug}' at {Project.project_dir(root, slug)}")
    print("Next: `ingest`")


def cmd_ingest(args: argparse.Namespace) -> None:
    root = Path.cwd()
    project = Project.load(root, args.slug)
    frames_dir = Project.project_dir(root, args.slug) / "frames" / "raw"
    video_path = Path(project.source_video_path)

    print(f"Detecting scenes in {video_path} (threshold={args.threshold})...")
    scenes = detect.ingest(
        video_path, frames_dir, threshold=args.threshold, candidates_per_scene=args.candidates_per_scene
    )
    project.scenes = scenes
    project.save(root)
    print(f"Detected {len(scenes)} scene(s). Run `review` next.")


def cmd_review(args: argparse.Namespace) -> None:
    review.review_project(Path.cwd(), args.slug)


def cmd_restyle(args: argparse.Namespace) -> None:
    root = Path.cwd()
    project = Project.load(root, args.slug)
    provider_name = args.provider or project.style.default_restyle_provider
    provider = get_provider(provider_name)
    styled_dir = Project.project_dir(root, args.slug) / "styled"

    if args.check:
        if provider_name != "manual":
            print("--check only applies to the manual provider.")
            return
        changed = 0
        for ref in project.reference_images:
            if ref.restyle_status != "pending_manual" or not ref.styled_frame_path:
                continue
            if provider.check(Path(ref.styled_frame_path)):
                ref.restyle_status = "completed"
                changed += 1
        project.save(root)
        print(f"{changed} reference image(s) marked completed.")
        return

    if not project.reference_images:
        print("No reference images yet. Run `review` and flag some with `r <tag> <ref_id> <description>` first.")
        return

    for ref in project.reference_images:
        if ref.restyle_status == "completed":
            continue
        dest = styled_dir / f"{ref.ref_id}.jpg"
        result = provider.restyle(Path(ref.raw_frame_path), project.style.style_phrase, dest)
        ref.styled_frame_path = str(result.output_path)
        ref.restyle_status = result.status
        ref.restyle_provider = result.provider
        print(f"{ref.ref_id}: {result.status} - {result.message}")

    project.save(root)
    if provider_name == "manual":
        print("\nRun `restyle --check` after you've manually restyled and overwritten the files above.")


def cmd_shots(args: argparse.Namespace) -> None:
    shots_module.assign_shots(Path.cwd(), args.slug)


def cmd_generate_shotlist(args: argparse.Namespace) -> None:
    root = Path.cwd()
    project = Project.load(root, args.slug)

    warnings = lint.lint_project(project)
    if warnings:
        print(f"{len(warnings)} lint warning(s):")
        for w in warnings:
            print(f"  [{w.shot_id}] {w.message}")
        if args.strict:
            print("\n--strict set: fix the warnings above before generating.")
            return
        print()

    out_dir = Project.project_dir(root, args.slug) / "output"
    md_path = out_dir / "shotlist.md"
    html_path = out_dir / "storyboard.html"
    render_markdown.render_markdown(project, md_path)
    render_html.render_storyboard(project, html_path)
    print(f"Wrote {md_path}")
    print(f"Wrote {html_path}")


def cmd_status(args: argparse.Namespace) -> None:
    root = Path.cwd()
    project = Project.load(root, args.slug)

    total_scenes = len(project.scenes)
    reviewed = sum(1 for s in project.scenes if s.reviewed)
    kept = sum(1 for s in project.scenes if s.kept)
    refs = len(project.reference_images)
    refs_done = sum(1 for r in project.reference_images if r.restyle_status == "completed")
    shots_total = len(project.shots)
    shots_prompted = sum(1 for s in project.shots if s.status == "prompted")

    print(f"Project: {project.style.project_name} ({project.slug})")
    print(f"Scenes:      {reviewed}/{total_scenes} reviewed, {kept} kept")
    print(f"References:  {refs_done}/{refs} restyled  (target 8-12 total)")
    print(f"Shots:       {shots_prompted}/{shots_total} fully detailed")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="silentremake")
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init", help="Create a new project from a source .mp4")
    p_init.add_argument("slug")
    p_init.add_argument("--source", required=True, help="Path to the source .mp4")
    p_init.add_argument("--style", required=True, help="Locked style phrase (e.g. 'A24 horror')")
    p_init.add_argument("--lighting", required=True, help="Locked lighting phrase")
    p_init.add_argument("--grade", required=True, help="Locked film grain/grade phrase")
    p_init.add_argument("--name", help="Display project name (defaults to slug)")
    p_init.add_argument("--genre", choices=["drama", "comedy"], default="drama")
    p_init.add_argument("--provider", choices=["manual", "gemini", "local"], default="manual")
    p_init.set_defaults(func=cmd_init)

    p_ingest = sub.add_parser("ingest", help="Detect scenes and extract candidate frames")
    p_ingest.add_argument("slug")
    p_ingest.add_argument("--threshold", type=float, default=27.0)
    p_ingest.add_argument("--candidates-per-scene", type=int, default=3)
    p_ingest.set_defaults(func=cmd_ingest)

    p_review = sub.add_parser("review", help="Interactively keep/skip/reference-flag detected scenes")
    p_review.add_argument("slug")
    p_review.set_defaults(func=cmd_review)

    p_restyle = sub.add_parser("restyle", help="Restyle curated reference images with the locked style phrase")
    p_restyle.add_argument("slug")
    p_restyle.add_argument("--provider", choices=["manual", "gemini", "local"], default=None)
    p_restyle.add_argument("--check", action="store_true", help="Check manual restyles for completion")
    p_restyle.set_defaults(func=cmd_restyle)

    p_shots = sub.add_parser("shots", help="Assign shot type/camera/action/anchor per kept shot")
    p_shots.add_argument("slug")
    p_shots.set_defaults(func=cmd_shots)

    p_gen = sub.add_parser("generate-shotlist", help="Lint + render the markdown shot list and HTML storyboard")
    p_gen.add_argument("slug")
    p_gen.add_argument("--strict", action="store_true", help="Abort on lint warnings")
    p_gen.set_defaults(func=cmd_generate_shotlist)

    p_status = sub.add_parser("status", help="Show progress summary")
    p_status.add_argument("slug")
    p_status.set_defaults(func=cmd_status)

    return parser


def main(argv: list[str] | None = None) -> None:
    load_dotenv(Path.cwd() / ".env")
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)
