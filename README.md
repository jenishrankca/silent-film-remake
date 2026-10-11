# Silent Film Remake — Phase 1: Shot List & Storyboard Generator

Turns a silent film `.mp4` into a director-ready shot list + storyboard package,
following the methodology in [ai-direction-guide.md](ai-direction-guide.md): pull
reference frames, lock a style phrase, build a shot list anchored to those
references, and fill a fixed prompt template you paste into Seedance/Veo3/Kling
(or any other tool) yourself. No video is generated automatically in this phase.

## Setup

This machine has **two Python installs**: `python3` on PATH is a clean 3.14 with
no packages; `python` / `py -3.13` is 3.13.5 and already has `opencv-python` and
`scenedetect` installed. Create the venv explicitly with the 3.13 launcher so you
don't end up with a mismatched environment:

```
py -3.13 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

ffmpeg is **not required** — frame extraction uses OpenCV's own decoder.

## Workflow

```
python -m silentremake init <slug> --source <film.mp4> ^
    --style "Eggers-style desaturated 35mm" ^
    --lighting "harsh side lighting, deep shadow" ^
    --grade "35mm film grain, desaturated teal-grey grade" ^
    [--name "Display Name"] [--genre drama|comedy] [--provider manual|gemini|local]

python -m silentremake ingest <slug> [--threshold 27] [--candidates-per-scene 3]
python -m silentremake review <slug>
python -m silentremake restyle <slug> [--provider manual|gemini|local] [--check]
python -m silentremake shots <slug>
python -m silentremake generate-shotlist <slug> [--strict]
python -m silentremake status <slug>
```

1. **init** — creates `projects/<slug>/project.yaml` with your locked style bible.
   The `--style` / `--lighting` / `--grade` phrases are stored once and reused
   identically in every shot's prompt (this is the guide's core consistency rule).
2. **ingest** — runs scene-cut detection over the source video and pulls 3
   candidate frames per detected scene into `projects/<slug>/frames/raw/`.
3. **review** — opens an HTML overview of all candidate frames in your browser,
   then walks you through each scene in the terminal:
   - `k` keep this scene as a shot
   - `s` skip it
   - `r <tag> <ref_id> <description>` flag the current frame as one of your 8-12
     locked reference images (tag: `character` / `set` / `prop`)
   - `c <n>` pick a different candidate frame
   - `t <seconds>` grab an arbitrary frame at a timestamp
   - `q` save and quit (resumes where you left off next time)
4. **restyle** — runs your curated reference images through a restyle provider:
   - `manual` (default): copies the raw frame + writes a `.prompt.txt` sidecar
     with the exact locked style phrase — paste it into Leonardo.ai, Bing Image
     Creator, or any web tool, overwrite the copied file with the result, then
     run `restyle --check` to mark it complete.
   - `gemini`: calls Google AI Studio's image endpoint directly. Requires
     `GEMINI_API_KEY`, either as a real environment variable or in a `.env`
     file at the repo root (`GEMINI_API_KEY=...`, gitignored, auto-loaded on
     every command).
   - `local`: calls a locally-running Automatic1111 Stable Diffusion WebUI
     (`--api` flag enabled). Point `LOCAL_SD_URL` at it if not on the default
     `http://127.0.0.1:7860` (also settable via `.env`).
5. **shots** — a second pass over every kept shot: set shot type, camera move,
   the anchor reference image, character count, and a one-sentence action
   description. Character count >= 2 auto-generates a "expect drift" warning.
6. **generate-shotlist** — lints every shot (flags vague actions, missing
   anchors, unset camera/shot type — the guide's "decision vs. instruction"
   check) then writes:
   - `projects/<slug>/output/shotlist.md` — the full doc, one section per shot,
     each with a copy-paste-ready generation prompt.
   - `projects/<slug>/output/storyboard.html` — a browsable grid view of the
     same shots.
7. **status** — quick progress summary at any point.

Re-running `generate-shotlist` any time (including after hand-editing
`project.yaml`) is safe — it's a pure re-render.

## What this does NOT do (yet)

No API calls generate actual video clips. You take `shotlist.md` /
`storyboard.html` into Seedance / Veo3 / Kling / CapCut yourself, per the
guide. A later phase could add direct video-gen API calls on top of this same
project data — the schema (`schema_version` field, additive-only) is designed
to support that without a rewrite.
