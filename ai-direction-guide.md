# AI Direction Guide
### For remaking public domain silent films (Buster Keaton, Caligari, Nosferatu, etc.)

---

## 1. The Core Principle: You're a Director, Not a Prompt-Writer

The biggest mistake with AI video is treating it like a vending machine (type words → get movie). Treat it like directing a shoot: you control **references, shot lists, and continuity** — the AI is your camera and actors, not your creative decision-maker.

**Golden rule:** Every decision you can lock *before* generating (character look, set, lighting, camera style) is one less thing the AI has to guess — and guessing is where consistency breaks.

---

## 2. Pre-Production (Do This BEFORE Opening Any Video Tool)

### Step 1 — Pull reference frames from the source film
- Use archive.org to get the original film
- Screenshot 8-12 key frames: your main character's clearest close-up, the primary set/location from 2-3 angles, any iconic prop or composition
- This is your **free storyboard** — the original already solved blocking and composition for you

### Step 2 — Build your reference sheet
- Run each screenshot through an image model (Leonardo.ai free tier, Bing Image Creator) with your chosen style prompt (e.g. "A24 horror," "Eggers-style desaturated 35mm")
- Keep the SAME style-prompt wording across every image — this is what keeps your whole film visually unified
- Save these restyled images — they are your locked references for every shot

### Step 3 — Write a shot list, not a script
For each beat, note only:
- Which reference image anchors it
- Camera move (static / slow push-in / handheld / locked-off)
- What happens in the shot (one sentence, plain language)

Example:
> Shot 4 — Cesare's introduction | Anchor: Cesare_ref_02 | Camera: slow push-in, locked-off | Cesare opens his eyes for the first time in the cabinet

---

## 3. Prompting Structure (Use This Every Time)

Order matters. Follow this sequence for every prompt:

1. **Shot type** — extreme close-up / wide / medium
2. **Subject + action** — who, doing what
3. **Camera movement** — static, dolly, tracking, locked-off
4. **Lighting** — practical only, side lighting, golden hour, Rembrandt lighting
5. **Atmosphere/style** — film grain, aspect ratio, color grade, your locked style phrase

**Template:**
`[shot type] of [subject] [action], [camera move], [lighting], [style/grain/grade]`

**Example:**
`Medium shot of a gaunt asylum director standing in a doorway, static locked-off camera, harsh side lighting with deep shadow, 35mm film grain, desaturated teal-grey grade`

Keep the lighting + style/grade language **identical across every prompt in the film** — this is the single biggest lever for visual consistency, more than the tool itself.

---

## 4. Tool Selection (What to Use When)

| Tool | Use it for | Why |
|---|---|---|
| **Seedance 2.0** | Your main workhorse — most shots | Best free character-lock consistency, 100 free daily credits, 1080p, no watermark |
| **Veo 3** | Wide establishing/atmospheric shots | Best raw realism, native audio, free via Google AI Studio |
| **Kling 3.0** | Multi-character interaction shots | "Elements" feature handles multi-subject scenes better than most |

**Workflow:** generate a small batch (3-5 takes) per shot, keep the best one, move on. Don't over-generate chasing perfection — diminishing returns kick in fast.

---

## 5. Directing for Consistency (The Hard Part)

- **Always feed your reference image** into image-to-video mode — never generate a character from a text prompt alone if you already have a locked reference
- **One character in frame = easy.** Two characters interacting = expect drift at the point of contact; plan for a manual touch-up or a reaction-shot workaround (cut away before the interaction gets complex)
- **Reuse your exact style-prompt language** every single time — treat it like a locked "look bible" you copy-paste, not something you rewrite per shot
- **Match cut on action:** end one AI clip on a pose/position that the next clip can pick up from — this hides seams between separately-generated clips

---

## 6. Directing for Comedy Specifically (Keaton/Mr. Bean style)

Since gag-driven comedy relies on **timing and physical clarity**, not dialogue:
- Keep shots WIDE enough to see the full physical gag (don't over-crop on close-ups)
- Static or slow camera moves — a shaky/handheld camera undercuts the deadpan stillness that makes silent comedy funny
- Direct for the "beat before the gag" — a half-second pause/held expression before the payoff is what sells physical comedy; specify this in your prompt ("holds still, deadpan expression, before...")
- You can likely skip AI voice generation entirely here — score + sound effects only, which cuts a full production step and cost

---

## 7. Post-Production Checklist

- [ ] Assemble clips in CapCut (free) in shot-list order
- [ ] Add score (Suno, since you already have Premium)
- [ ] Add narration only if the format needs it (skip for pure physical comedy)
- [ ] Color-match any clips that drifted in grade during generation
- [ ] Export and post natively to each platform (don't just link — native uploads perform better everywhere)

---

## 8. The One Habit That Matters Most

Before generating anything, ask: **"Am I giving the AI a decision to make, or am I giving it an instruction to execute?"**

If the AI is deciding (what does this character look like? how is this scene lit?), you haven't finished pre-production yet. Go back to your reference sheet. The guide above exists to get you to "instruction to execute" on every single shot.
