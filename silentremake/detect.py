"""Scene detection + representative key-frame extraction from a source .mp4."""
from __future__ import annotations

from pathlib import Path

import cv2
from scenedetect import open_video, SceneManager, ContentDetector

from .project import CandidateFrame, DetectedScene


def _sharpness(image) -> float:
    """Laplacian-variance sharpness score; higher = less blurry."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


def detect_scenes(video_path: Path, threshold: float = 27.0) -> list[tuple[float, float]]:
    """Returns list of (start_seconds, end_seconds) per detected scene."""
    video = open_video(str(video_path), backend="opencv")
    scene_manager = SceneManager()
    scene_manager.add_detector(ContentDetector(threshold=threshold))
    scene_manager.detect_scenes(video=video)
    scene_list = scene_manager.get_scene_list()
    if not scene_list:
        duration_s = video.duration.get_seconds() if video.duration else 0.0
        return [(0.0, duration_s)]
    return [(start.get_seconds(), end.get_seconds()) for start, end in scene_list]


def extract_candidates(
    video_path: Path,
    scene_index: int,
    start_s: float,
    end_s: float,
    out_dir: Path,
    candidates_per_scene: int = 3,
) -> list[CandidateFrame]:
    """Grab representative frames at ~10%/50%/90% through the scene, sharpness-scored."""
    out_dir.mkdir(parents=True, exist_ok=True)
    cap = cv2.VideoCapture(str(video_path))
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0

    fractions = [0.1, 0.5, 0.9][:candidates_per_scene] if candidates_per_scene <= 3 else [
        i / (candidates_per_scene + 1) for i in range(1, candidates_per_scene + 1)
    ]

    candidates: list[CandidateFrame] = []
    for i, frac in enumerate(fractions):
        timestamp_s = start_s + (end_s - start_s) * frac
        frame_number = int(timestamp_s * fps)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        ok, frame = cap.read()
        if not ok:
            continue
        sharpness = _sharpness(frame)
        filename = f"scene{scene_index:04d}_cand{i}.jpg"
        out_path = out_dir / filename
        cv2.imwrite(str(out_path), frame)
        candidates.append(
            CandidateFrame(
                path=str(out_path),
                timestamp_s=timestamp_s,
                frame_number=frame_number,
                sharpness=sharpness,
            )
        )
    cap.release()
    return candidates


def grab_frame_at(video_path: Path, timestamp_s: float, out_path: Path) -> CandidateFrame:
    """Grab a single frame at an arbitrary timestamp (used by the manual re-pick command)."""
    cap = cv2.VideoCapture(str(video_path))
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    frame_number = int(timestamp_s * fps)
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
    ok, frame = cap.read()
    if not ok:
        cap.release()
        raise ValueError(f"Could not read frame at {timestamp_s}s from {video_path}")
    sharpness = _sharpness(frame)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out_path), frame)
    cap.release()
    return CandidateFrame(
        path=str(out_path),
        timestamp_s=timestamp_s,
        frame_number=frame_number,
        sharpness=sharpness,
    )


def ingest(
    video_path: Path,
    frames_dir: Path,
    threshold: float = 27.0,
    candidates_per_scene: int = 3,
) -> list[DetectedScene]:
    """Full ingest pass: detect scenes, pull candidate frames for each."""
    scene_bounds = detect_scenes(video_path, threshold=threshold)
    scenes: list[DetectedScene] = []
    for idx, (start_s, end_s) in enumerate(scene_bounds):
        candidates = extract_candidates(
            video_path, idx, start_s, end_s, frames_dir, candidates_per_scene
        )
        scenes.append(
            DetectedScene(scene_index=idx, start_s=start_s, end_s=end_s, candidates=candidates)
        )
    return scenes
