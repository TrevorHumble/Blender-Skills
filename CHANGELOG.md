# Changelog

All notable changes to this repository are documented here. Format follows [Keep a Changelog](https://keepachangelog.com/). Version numbers per skill are tracked at the top of each skill document.

## [Unreleased]

## [0.2.0] — 2026-05-11

### Added
- **Skill 02: Render & Assembly** (v2.4.0) — sequential headless rendering with mid-render Haiku 4.5 vision verification, per-scene abort on consecutive failures, pass-isolated render output folders, and Blender VSE assembly into final video deliverable. Six formal artist check-ins. Migrated from [TrevorHumble/story-pipeline](https://github.com/TrevorHumble/story-pipeline) (formerly Production Skill 02 in the story analysis pipeline).
- Reference scripts: `render_scene.py` (per-scene headless render), `render_all.sh` (batch wrapper), `assemble_vse.py` (VSE timeline assembly).
- `skills/scripts/` directory for reference implementations shared across skills.

## [0.1.0] — 2026-05-11

### Added
- **Skill 01: Character Disassembly** (v1.0.0) — workflow for building standalone severable body parts from a fully-rigged Auto-Rig Pro character. Source character stays untouched; each part is a self-contained mesh + independent trimmed armature that can be appended into a scene as a free-floating piece. Proven on Florence's right hand for the *Catalysis* short film.
- Initial repo structure (`skills/`, `README.md`, `LICENSE`, `CHANGELOG.md`).
