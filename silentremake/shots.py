"""Second review pass: assign shot type / camera move / action / anchor ref per kept shot."""
from __future__ import annotations

from pathlib import Path

from .project import Project

FIELD_HELP = (
    "Valid shot_type: extreme close-up, close-up, medium, wide, establishing, extreme wide\n"
    "Valid camera_move: static, slow push-in, handheld, locked-off, dolly, tracking\n"
    "Leave a field blank to keep its current value. Type `skip` at the label prompt to move on, "
    "`quit` at any prompt to stop and save.\n"
)


def assign_shots(root: Path, slug: str) -> None:
    project = Project.load(root, slug)

    if not project.reference_images:
        print("No reference images yet. Run `review` and flag some with `r <tag> <ref_id> <description>` first.")
        return

    pending = [s for s in project.shots if s.status == "kept"]
    if not pending:
        print("No shots pending detail assignment. Run `review` first if you haven't kept any shots yet.")
        return

    print(f"{len(pending)} shot(s) need detail. Reference images:")
    for r in project.reference_images:
        print(f"  {r.ref_id} ({r.tag}): {r.description}")
    print()
    print(FIELD_HELP)

    def _stop() -> bool:
        project.save(root)
        print("Saved.")
        return True

    for shot in pending:
        print(f"\n--- {shot.id} (scene {shot.scene_index}) - {shot.raw_frame_path}")

        label = input(f"Label [{shot.label}]: ").strip()
        if label.lower() == "quit":
            _stop()
            return
        if label.lower() == "skip":
            continue
        if label:
            shot.label = label

        anchor = input(f"Anchor ref_id [{shot.anchor_ref_id or ''}]: ").strip()
        if anchor.lower() == "quit":
            _stop()
            return
        if anchor:
            if not project.get_ref(anchor):
                print(f"Warning: '{anchor}' is not a known ref_id (saved anyway).")
            shot.anchor_ref_id = anchor

        shot_type = input(f"Shot type [{shot.shot_type}]: ").strip()
        if shot_type.lower() == "quit":
            _stop()
            return
        if shot_type:
            shot.shot_type = shot_type

        camera_move = input(f"Camera move [{shot.camera_move}]: ").strip()
        if camera_move.lower() == "quit":
            _stop()
            return
        if camera_move:
            shot.camera_move = camera_move

        char_count = input(f"Character count [{shot.character_count}]: ").strip()
        if char_count.lower() == "quit":
            _stop()
            return
        if char_count:
            try:
                shot.character_count = int(char_count)
            except ValueError:
                print("Invalid number, keeping previous value.")

        action = input(f"Action sentence [{shot.subject_action}]: ").strip()
        if action.lower() == "quit":
            _stop()
            return
        if action:
            shot.subject_action = action

        if project.style.genre_mode == "comedy":
            beat = input(f"Beat before gag [{shot.beat_before_gag}]: ").strip()
            if beat.lower() == "quit":
                _stop()
                return
            if beat:
                shot.beat_before_gag = beat

        shot.status = "anchored" if shot.anchor_ref_id else "kept"
        if shot.anchor_ref_id and shot.shot_type and shot.camera_move and shot.subject_action:
            shot.status = "prompted"

        project.save(root)
        print(f"Saved {shot.id}.")

    project.save(root)
    print("\nAll pending shots processed. Run `generate-shotlist` next.")
