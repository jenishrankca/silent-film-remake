"""Interactive terminal review loop: keep/skip/reference-flag/re-pick detected scenes."""
from __future__ import annotations

import webbrowser
from pathlib import Path

from .project import Project, Shot, ReferenceImage
from . import detect
from .render_html import Card, render_grid

HELP = "Commands: [k]eep  [s]kip  [r] <tag> <ref_id> <description>  [c] <n>  [t] <seconds>  [q]uit"


def _write_overview(project: Project, out_path: Path) -> None:
    cards: list[Card] = []
    for scene in project.scenes:
        for i, c in enumerate(scene.candidates):
            body = [f"t={c.timestamp_s:.1f}s", f"sharpness={c.sharpness:.1f}"]
            if scene.chosen_frame_path == c.path:
                body.append("CHOSEN")
            cards.append(
                Card(image_path=c.path, heading=f"Scene {scene.scene_index} · cand {i}", body_lines=body)
            )
    render_grid(
        title=f"{project.style.project_name} — Review Overview",
        subtitle="Candidate frames per detected scene (browse here while deciding in the terminal)",
        cards=cards,
        out_path=out_path,
    )


def review_project(root: Path, slug: str) -> None:
    project = Project.load(root, slug)
    video_path = Path(project.source_video_path)
    frames_dir = Project.project_dir(root, slug) / "frames" / "raw"
    overview_path = Project.project_dir(root, slug) / "output" / "review_overview.html"

    pending = [s for s in project.scenes if not s.reviewed]
    if not pending:
        print("All scenes already reviewed. Run `shots` next.")
        return

    _write_overview(project, overview_path)
    try:
        webbrowser.open(overview_path.resolve().as_uri())
    except Exception:
        pass

    print(f"{len(pending)} scene(s) to review. Overview: {overview_path}")
    print(HELP)

    ref_count = len(project.reference_images)

    for scene in pending:
        best = max(scene.candidates, key=lambda c: c.sharpness, default=None)
        chosen = scene.chosen_frame_path or (best.path if best else None)

        while True:
            print(f"\nScene {scene.scene_index}: {scene.start_s:.1f}s - {scene.end_s:.1f}s")
            for i, c in enumerate(scene.candidates):
                suggested = " <- suggested" if best and c.path == best.path else ""
                is_chosen = " [CHOSEN]" if c.path == chosen else ""
                print(f"  [{i}] {c.path}  t={c.timestamp_s:.1f}s sharpness={c.sharpness:.1f}{suggested}{is_chosen}")
            print(f"  References so far: {ref_count} (target 8-12)")

            raw = input("> ").strip()
            if not raw:
                continue
            parts = raw.split(maxsplit=3)
            cmd = parts[0].lower()

            if cmd == "q":
                project.save(root)
                print("Saved. Resume later with `review`.")
                return

            if cmd == "c" and len(parts) >= 2:
                try:
                    idx = int(parts[1])
                    chosen = scene.candidates[idx].path
                    scene.chosen_frame_path = chosen
                    print(f"Chosen candidate set to [{idx}]")
                except (ValueError, IndexError):
                    print("Invalid candidate index.")
                continue

            if cmd == "t" and len(parts) >= 2:
                try:
                    ts = float(parts[1])
                    out_path = frames_dir / f"scene{scene.scene_index:04d}_manual_{len(scene.candidates)}.jpg"
                    frame = detect.grab_frame_at(video_path, ts, out_path)
                    scene.candidates.append(frame)
                    chosen = frame.path
                    scene.chosen_frame_path = chosen
                    print(f"Grabbed frame at {ts}s -> {frame.path}")
                except ValueError as e:
                    print(f"Error: {e}")
                continue

            if cmd == "r" and len(parts) >= 4:
                tag, ref_id, description = parts[1], parts[2], parts[3]
                if not chosen:
                    print("No frame chosen yet - use `c <n>` or `t <seconds>` first.")
                    continue
                if project.get_ref(ref_id):
                    print(f"ref_id '{ref_id}' already exists, pick another.")
                    continue
                project.reference_images.append(
                    ReferenceImage(ref_id=ref_id, tag=tag, description=description, raw_frame_path=chosen)
                )
                ref_count += 1
                print(f"Added reference '{ref_id}' ({ref_count} total).")
                continue

            if cmd == "k":
                if not chosen:
                    print("No frame chosen yet - use `c <n>` or `t <seconds>` first.")
                    continue
                scene.chosen_frame_path = chosen
                scene.kept = True
                scene.reviewed = True
                shot_num = len(project.shots) + 1
                shot = Shot(
                    id=f"shot_{shot_num:03d}",
                    order=shot_num,
                    label=f"Scene {scene.scene_index}",
                    raw_frame_path=chosen,
                    scene_index=scene.scene_index,
                    status="kept",
                )
                project.shots.append(shot)
                project.save(root)
                print(f"Kept as {shot.id}.")
                break

            if cmd == "s":
                scene.reviewed = True
                scene.kept = False
                project.save(root)
                print("Skipped.")
                break

            print(f"Unknown command. {HELP}")

    project.save(root)
    print("\nAll scenes reviewed. Run `shots` next to fill in per-shot camera/action details.")
