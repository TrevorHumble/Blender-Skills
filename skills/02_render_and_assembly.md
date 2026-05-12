# Skill 02 — Headless Rendering, Mid-Render Verification, and VSE Assembly

> **v2.4.0 update (2026-05-10):** Render output now uses a pass-isolated folder structure (`renders/<pass_type>/<pass_instance>/<scene_label>/`) so multiple passes can coexist without overwriting. The `render_scene.py` engine override has been removed — scripts now respect the engine saved in the .blend file unless explicitly overridden via `--engine`. See "Render output folder structure" section below.

> **Migrated from [TrevorHumble/story-pipeline](https://github.com/TrevorHumble/story-pipeline)** in v3.0.0 of that repo. This skill was originally Production Skill 02 in the story analysis pipeline. It lives here because it's a Blender rendering operation, not a story analysis step. The upstream pipeline's scene scaffolding phase produces the input files for this skill.

## Purpose

Take a folder of scaffolded, posed Blender scene files (the output of scene scaffolding + the artist's posing work) and produce a deliverable video file. This is the final mechanical step before delivery: no creative decisions are made here; the artist's poses, cameras, and lighting are simply executed at render time, then stitched together in canonical order.

This skill is **deliberately conservative**. Rendering is the slowest mechanical step in the pipeline, and failure recovery costs the most time. We render scenes **one at a time, in canonical order**, verify each scene mid-render and post-render, and stop immediately on structural failure. For indie animation where one tool, one machine, and a single artist's attention all coordinate, sequential-with-verification is the right tradeoff.

The skill uses a small LLM agent (Haiku 4.5 vision) as a *render supervisor* — sampling rendered frames during the render itself, flagging mechanical failures (black frames, missing characters, broken geometry), and aborting individual scenes that fail repeatedly. The supervisor's job is bounded to **render correctness**, never creative critique. The artist remains the only judge of pose, framing, expression, mood.

## Scope and what is deliberately deferred

**Included:**
- Pre-flight checks per scene (camera, frame range, render settings)
- Sequential per-scene rendering using a Python frame-by-frame loop (not `bpy.ops.render.render(animation=True)`)
- **Mid-render Haiku vision verification** at every Nth frame (default 24)
- Per-scene abort on consecutive vision-check failures (default 3 in a row)
- Post-render file-system verification per scene
- Blender VSE assembly of the rendered sequences into one timeline
- Watch-v1, identify-fixes, re-render, re-assemble loop
- Final export to a video file

**Deferred to future skills:**
- **Per-scene compositing.** For an animatic rendered with Workbench (clay-look, unshaded), no compositing is needed. For final film, each scene gets its own compositor node tree consuming its own multilayer EXR. Future skill.
- **Audio mixing.** Animatic scratch audio is dropped into the VSE manually after assembly. Final film sound design is a dedicated DAW pass.
- **Color grading.** Global VSE-level grade is a future delivery skill.
- **Creative critique of poses, framing, expressions, mood.** The vision-check supervisor is scoped to render correctness only. Creative judgment is the artist's.

If the artist asks for compositing, sound design, or creative critique inside this skill, **do not attempt it inline**. Stop, name the work that's outside scope, and defer to a future skill or a manual pass.

## Inputs

- A folder of Blender scene files in canonical naming convention
- Each scene file must have:
  - An active camera positioned for the shot (artist's responsibility)
  - Frame range (`scene.frame_start`, `scene.frame_end`) set
  - Lighting set up (or, if Workbench, lighting is irrelevant)
  - Render settings consistent with project standards
- Path to the Blender executable
- An output directory for rendered image sequences
- A target file path for the assembled VSE project
- A target file path for the final exported video
- **For mid-render verification:**
  - `ANTHROPIC_API_KEY` environment variable
  - The `anthropic` Python SDK installed in Blender's bundled Python (or a wrapper script that subprocess-calls a system Python with it)
  - Per-scene description data (extracted from `directors_notes.md`) listing expected characters and what's nominally happening in the scene

## Stop protocols (formal user check-ins)

This skill has **six required check-ins** with the artist. Do not advance past any of them autonomously without confirmation.

| Check-in | When | What's being confirmed |
|---|---|---|
| **CI-1: Pre-flight** | Before Step 1 | Each scene's camera, frame range, lighting, and render settings are correct. |
| **CI-2: Settings lock** | Before Step 2 | The chosen render engine, resolution, frame rate, and output format are agreed and frozen. |
| **CI-3: Mid-render checkpoint** | After every 3rd scene completes | Spot-check the rendered sequences. If anything looks broken, stop and debug. |
| **CI-3.5: Vision-flag review (NEW)** | Whenever a scene aborts mid-render OR after batches with flagged scenes | Artist reviews scenes the Haiku supervisor flagged or aborted. Decides which to re-render. |
| **CI-4: Pre-assembly** | Before Step 4 | Every scene rendered successfully. Frame counts match. No accidental 1-frame renders. |
| **CI-5: Watch-v1 review** | After Step 5 | The artist watches end-to-end and names which scenes need re-rendering or re-blocking. |

Each check-in is a hard stop.

## Two failure tiers — different responses

| Failure type | Source | Response |
|---|---|---|
| **Structural failure** | File-system check (no frames written, render engine error, frame count off) | **STOP THE WHOLE RUN.** Something is broken with setup. |
| **Vision-check failure** | Haiku supervisor flags a sample frame | **MARK SCENE FAILED, CONTINUE TO NEXT.** Could be false positive; don't punish the artist by blocking the rest of the film. |
| **Vision-check abort** | 3 consecutive vision failures within a single scene | **ABORT THE SCENE'S RENDER, MARK ABORTED, CONTINUE TO NEXT.** Save remaining render time for other scenes. |

## Architecture note — Python loop is the primitive

In v2.2.0 of this skill, the rendering primitive was `bpy.ops.render.render(animation=True)` — Blender's animation render call, opaque to Python during execution. v2.3.0 inverts this: **the rendering primitive is a Python frame-by-frame loop**, with `bpy.ops.render.render(write_still=True)` as the inner call per frame. This is required to enable mid-render verification, but it has other benefits:

- **Clean cancellation.** A scene aborts with `break` rather than depending on `bpy.ops.render.render_cancel()` semantics.
- **Resume-from-frame-N.** If a scene aborted at frame 48, resume from frame 49 once the artist fixes whatever broke. Trivially possible; not possible with `animation=True`.
- **Per-frame error handling.** Python catches per-frame errors directly without needing render handlers.

Cost: per-frame Python overhead is roughly 10–20% slower than animation render for fast engines (EEVEE). For Workbench (~0.1s/frame) and Cycles (~30s/frame), the overhead is invisible.

## Instructions

### Step 1 — Pre-flight every scene (CI-1 happens after this)

For each scene file in canonical order, run a non-destructive inspection that prints:

- Active camera name (or `[NONE]` — blocker)
- Frame start / frame end / total frame count
- Render engine currently set
- Resolution X x Y at current `resolution_percentage`
- Output format (PNG / OPEN_EXR / OPEN_EXR_MULTILAYER)
- Number of objects in the active scene
- Whether the named character collections are present

Output a table the artist can scan. **CI-1 pause:** artist confirms before Step 2.

### Step 2 — Lock render settings (CI-2 happens after this)

Choose, name, and document for this render pass:

- **Engine** — Workbench (animatic), EEVEE / EEVEE Next (lookdev), Cycles (final film)
- **Resolution percentage** — 50 for animatic, 100 for final
- **Frame rate** — typically 24 fps
- **File format** — `PNG` for sequences (recommended for animatic), or `OPEN_EXR_MULTILAYER` (recommended for final film with downstream compositing). The vision check handles both.
- **Color management view transform** — note what's set; for HDR EXR, this affects what the vision check sees after PNG conversion
- **Vision verification settings** — sample interval (default 24), consecutive-fail abort threshold (default 3), model (default `claude-haiku-4-5-20251001`)

**CI-2 pause:** artist confirms.

### Step 3 — Render scenes one at a time, in canonical order (Python loop)

For each scene in canonical order:

1. Open the scene in headless Blender
2. Apply locked settings from Step 2
3. Enter the per-frame render loop:
   ```
   For frame in [scene.frame_start .. scene.frame_end]:
     scene.frame_set(frame)
     bpy.ops.render.render(write_still=True)
     If sample frame (frame relative to scene_start, every Nth):
       Run Step 3.5 verification on this frame
       If 3 consecutive vision failures:
         break (abort this scene, mark ABORTED, continue to next scene)
   ```
4. After loop completes, run Step 3.6 file-system verification

### Step 3.5 — Vision verification (per sample frame)

For each sample frame (frame relative to scene start, multiple of `SAMPLE_INTERVAL`):

1. **Determine the image to send to Haiku:**
   - If output format is PNG/JPEG: use the rendered file directly
   - If output format is `OPEN_EXR` or `OPEN_EXR_MULTILAYER`: convert *just this one frame* to a temp PNG using `bpy.data.images.load()` + `image.save_render()`. The full EXR is preserved for downstream compositing.
2. **For multilayer EXR:** ensure the active render layer is the beauty / Combined pass before conversion. Other layers (Z, normal, AO) are unviewable to vision models.
3. **Apply scene's view transform** during conversion so HDR values tonemap into PNG's 8-bit range. `save_render()` handles this; raw `save()` does not.
4. **Call Haiku** with:
   - The rendered PNG
   - Per-scene context: scene name, expected characters, one-sentence description from `directors_notes.md`
   - **Tightly scoped prompt**: "Flag ONLY render-correctness problems. Examples of what to flag: completely black or empty frames, missing characters that should be present, obviously broken geometry, characters at obviously wrong scale. DO NOT flag pose quality, framing, expression, lighting mood, animation issues, or any creative judgment — those are out of scope."
   - Required output: `PASS` / `FAIL: <one-sentence reason>` only
5. **Process result:**
   - PASS -> reset consecutive_fails to 0
   - FAIL -> increment consecutive_fails; if >= 3, abort scene
6. **Cleanup:** if a temp PNG was created from EXR, delete it after the check
7. **Network/timeout handling:** Haiku call has a 10-second hard timeout. Timeout = treat as PASS (don't punish render for transient API issues). Log the timeout for visibility.

### Step 3.6 — Post-render file-system verification (per scene)

After the render loop completes (or aborts), verify:

- Output folder exists
- Number of frame files matches `frame_end - frame_start + 1` (or matches the actual rendered range if aborted)
- Frame 1 file size > 0 and reads as a valid file
- Last frame file size > 0 and reads as a valid file

If verification fails: **STOP THE WHOLE RUN.** Structural problem.

If verification passes but the scene was vision-aborted: log as ABORTED and continue to next scene.

### Step 3.7 — CI-3 / CI-3.5 mid-run check-ins

After every 3rd scene OR whenever a scene aborts:
- Surface progress to the artist
- List scenes COMPLETED, FLAGGED, ABORTED so far
- Artist can choose: continue, pause to debug a specific scene, stop the whole run

### Step 4 — Pre-assembly verification (CI-4 happens after this)

Generate a summary table:

| Scene | Expected frames | Actual frames | Vision checks | Vision fails | Status |
|---|---|---|---|---|---|
| Act.1-Scene.1-Apartment | 96 | 96 | 4 | 0 | READY |
| Act.1-Scene.5-Beach | 240 | 48 | 2 | 2 | ABORTED — re-render needed |
| ... |

**CI-4 pause:** artist confirms before assembly.

### Step 5 — Assemble VSE timeline

Open a new empty Blender file. For each rendered scene folder (in canonical sort order):

1. Add an Image Strip to the VSE timeline at channel 1
2. Point at the first frame; append the rest
3. Place strips end-to-end
4. Set scene `frame_start = 1`, `frame_end = total length`
5. Pre-configure timeline render output: MP4, H.264, target output path
6. Save as the assembly project file

### Step 6 — Watch v1 and identify fixes (CI-5)

Artist watches end-to-end. Names re-render targets and re-block targets.

### Step 7 — Iterate (re-render flagged scenes only)

Re-render only the named scenes. VSE strips refresh from disk automatically.

### Step 8 — Final export

From the assembly project, render the timeline. Filename includes version + date. Verify playback. Deliver.

## Standards

- **Sequential per-scene rendering only.** No parallel.
- **PNG sequences for animatic, EXR multilayer for final film.** Vision check handles both.
- **Per-scene output folders.** No collisions.
- **Naming convention preserved end to end** — scene file -> render folder -> VSE strip.
- **Version + date in final output filename.**
- **Compositing is deferred.** Refuse and point at future skill.
- **Vision supervisor is bounded to render correctness.** Refuse to expand its scope to creative critique. The boundary is paper-worthy.
- **Re-render flagged scenes only.** Don't re-render the full film.

## Failure modes to anticipate

| Symptom | Likely cause | Action |
|---|---|---|
| Scene renders 1 frame instead of N | Frame range never set | STOP; fix frame range; re-render scene |
| Scene renders but frames are all black | No active camera, or camera below ground | STOP; fix camera; re-render |
| Output folder is empty after render | Output filepath wasn't set | STOP; inspect `scene.render.filepath` |
| Workbench OK but EEVEE/Cycles look wrong | Materials missing | Out of scope; artist fixes shading |
| VSE assembly opens empty | `discover_scene_sequences()` couldn't find PNGs | Verify render output structure |
| Final video skips frames | VSE timeline `frame_end` set wrong | Re-run Step 5 |
| Final video has audio drop-outs | Audio not handled here | Out of scope |
| **Vision check flags every frame as FAIL** | Prompt drifted into creative critique mode, or Haiku is in a bad state | Inspect Haiku's flag reasons; if any mention pose/expression/framing/mood, the prompt has drifted — refuse and refine |
| **Vision check times out repeatedly** | Network or Anthropic API issue | Treats as PASS by default; surface to artist if pattern persists |
| **Vision check on EXR returns FAIL on every frame** | EXR->PNG conversion lost data, OR no view transform applied (raw HDR clipped to black/white) | Verify temp PNG looks visually right; ensure `save_render()` not `save()`; check view transform setting |
| **Multilayer EXR vision check confused** | Wrong layer being converted (e.g., depth pass instead of beauty) | Force active render layer to "Combined" before conversion |

## Teaching Moment

**What this means in plain English.** Rendering is the slowest mechanical step in animation production, and the one where the artist gives up direct visibility for hours at a time. The traditional fix is "stare at progress bars" — passive monitoring with no active intelligence. This skill puts a small, scoped LLM agent in the loop as a render supervisor: it watches the render produce frames, flags things that look mechanically wrong (black frames, missing characters, broken geometry), and aborts individual scenes that fail repeatedly so the artist can recover render time for the rest of the film.

**Why it matters in any production.** Two principles compound here:
1. *Sequential-with-verification beats parallel-then-debug for indie production.* Faster failure-recovery cycles are worth more than parallel happy-path speed when one human is the bottleneck.
2. *Bounded LLM supervision is different from LLM control.* The supervisor never decides anything creative — it only flags mechanical correctness. The artist still owns every craft decision. This boundary discipline is the same principle that runs through the analysis pipeline (show-don't-tell, surface-don't-prescribe). Applied recursively, the same model that wrote the analysis is now verifying the production output, with the same guardrails.

**How it operates here.** Per scene: render frame by frame. Every 24th frame, sample to Haiku with a tightly-scoped prompt. If 3 consecutive samples fail, abort the scene and move on. EXR sample frames get converted to PNG just-in-time (the full EXR is preserved for downstream compositing). File-system verification at the end catches structural failures the vision check would miss. The artist gets check-in points to review flags and decide what's a true positive, what's a false alarm, and what to re-render.

**Takeaway for the practitioner.** When automation is tempting in a slow, expensive stage (rendering, training, deployment), the right move is rarely "fire and forget." It's "fire, supervise with bounded intelligence, and give the human cheap checkpoints to intervene." The supervisor's bound matters more than its capability — a supervisor that knows what it is *not* allowed to judge is more useful than a supervisor that has opinions about everything.

---

**Implementation status:** v2.3.0 of this skill describes the design. The deterministic Python implementation (per-frame render loop, Haiku integration, EXR conversion, abort logic) is tracked as GitHub issues in this repo (migrated from story-pipeline).

---

## Render output folder structure (v2.4.0)

All rendered frames go under `<project>/renders/<pass_type>/<pass_instance>/<scene_label>/`. This keeps multiple render passes (animatic v1, v2, lookdev v1, final v1, etc.) isolated so later runs don't overwrite earlier ones.

### Tree

```
<project>/
├── renders/
│   ├── animatic/
│   │   ├── 2026-05-10_v1_workbench_540p/
│   │   │   ├── _meta.json
│   │   │   ├── _audit/
│   │   │   │   └── Act.1-Scene.1-Apartment.md
│   │   │   └── Act.1-Scene.1-Apartment/
│   │   │       ├── Act.1-Scene.1-Apartment_0001.png
│   │   │       └── ...
│   │   └── 2026-05-13_v2_workbench_540p/
│   ├── lookdev/
│   ├── final/
│   └── dailies/
├── comps/                    # future skill
├── exports/                  # final assembled video deliverables
│   └── animatic_v1_2026-05-15.mp4
└── Scenes/Draft 2/           # source .blend files
```

### Pass type vocabulary

- `animatic` — blocking pass, fast engine (Workbench), low resolution
- `lookdev` — material/lighting development, EEVEE, intermediate resolution
- `final` — production render, Cycles, full resolution, multilayer EXR for compositing
- `dailies` — ad-hoc test renders that don't need full pass-folder treatment (default when `--pass-type` is not specified)

### Pass instance naming

Format: `<YYYY-MM-DD>_<version>_<engine>_<resolution>[_<note>]`

Examples:
- `2026-05-10_v1_workbench_540p`
- `2026-05-13_v2_workbench_540p`
- `2026-06-01_lookdev_v1_eevee_720p`
- `2026-07-15_final_v1_cycles_1080p_exr`

Date-first sorting keeps the folders in chronological order by default. The metadata in the folder name lets you identify any pass at a glance without opening files.

### `_meta.json` schema

Written to each pass instance after the batch completes:

```json
{
  "pass_type": "animatic",
  "version": "v1",
  "engine": "BLENDER_WORKBENCH",
  "resolution_x": 1920,
  "resolution_y": 1080,
  "resolution_percentage": 50,
  "fps": 24,
  "started_at": "2026-05-10T01:08:37Z",
  "finished_at": "2026-05-10T01:55:00Z",
  "scenes": [
    {"label": "Act.1-Scene.1-Apartment", "frames": 200, "status": "COMPLETED"},
    {"label": "Act.1-Scene.2-BakedBean", "frames": 250, "status": "COMPLETED"}
  ],
  "vision_check_summary": {"total_checks": 0, "flags": 0, "aborts": 0}
}
```

### Engine override (v2.4.0)

In v2.3.0, `render_scene.py` had a hardcoded `ENGINE = "BLENDER_EEVEE_NEXT"` that force-set the engine before every render. This caused the 2026-05-09 first-run renders to use EEVEE despite the artist intending Workbench. Bug fixed in v2.4.0:

- **Default**: respect the engine saved in the .blend file. Do not modify it.
- **Override**: optional `--engine <NAME>` CLI arg to `render_scene.py`. When passed, set the engine before render and log: `=== Engine override: WORKBENCH (was BLENDER_EEVEE_NEXT in file)`
- **No override**: log `=== Using engine from file: <ENGINE>` so the artist sees what's actually being used

**Lesson encoded:** scripts that silently override saved settings cause hard-to-diagnose bugs. The artist's saved configuration is canonical; tooling respects it unless explicitly told otherwise.

---

**Implementation status:** v2.4.0 documents the new folder structure and engine policy. The actual code changes to `render_scene.py` and `render_all.sh` are tracked as issues in this repo.
