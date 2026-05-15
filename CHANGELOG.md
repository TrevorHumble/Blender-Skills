# Changelog

All notable changes to this repository are documented here. Format follows [Keep a Changelog](https://keepachangelog.com/). Version numbers per skill are tracked at the top of each skill document.

## [Unreleased]

## [0.4.0] — 2026-05-15

### Changed
- **Skill 02: Render & Assembly** bumped to v2.5.0 — added "Vision check — implementation reference" section with full contracts a developer needs to implement the Haiku supervisor: `directors_notes.md` schema, expected-characters format, per-frame context bundle, Anthropic Messages API contract (system prompt + user message structure), EXR→PNG conversion code pattern, and error-handling matrix beyond timeout (rate-limits, 4xx auth, 5xx server, network, malformed responses). Closes implementation-readiness gaps flagged in review.

## [0.3.0] — 2026-05-12

### Added
- **Skill 03: Body Part Swap Setup** (v1.0.0) — companion to Skill 01. Covers how to take a pre-built body parts library and wire it into scene files with visibility keyframes that flip a character between intact and severed states. Documents the shared-action bug (duplicated armatures sharing Actions) and the Blender 5.1 save-crash workaround (one keyframe target per invocation). Proven on three *Catalysis* scenes (London, Black Void, Ballroom).

## [0.2.0] — 2026-05-11

### Added
- **Skill 02: Render & Assembly** (v2.4.0) — sequential headless rendering with mid-render Haiku 4.5 vision verification, per-scene abort on consecutive failures, pass-isolated render output folders, and Blender VSE assembly into final video deliverable. Six formal artist check-ins. Migrated from [TrevorHumble/story-pipeline](https://github.com/TrevorHumble/story-pipeline) (formerly Production Skill 02 in the story analysis pipeline).
- Reference scripts: `render_scene.py` (per-scene headless render), `render_all.sh` (batch wrapper), `assemble_vse.py` (VSE timeline assembly).
- `skills/scripts/` directory for reference implementations shared across skills.

## [0.1.0] — 2026-05-11

### Added
- **Skill 01: Character Disassembly** (v1.0.0) — workflow for building standalone severable body parts from a fully-rigged Auto-Rig Pro character. Source character stays untouched; each part is a self-contained mesh + independent trimmed armature that can be appended into a scene as a free-floating piece. Proven on Florence's right hand for the *Catalysis* short film.
- Initial repo structure (`skills/`, `README.md`, `LICENSE`, `CHANGELOG.md`).
