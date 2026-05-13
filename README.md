# Blender Skills

Production-tested Blender workflows for indie animated film work. Each skill is a self-contained Markdown document describing a single complex Blender operation — what it does, when to use it, the step-by-step phases, the artist check-in points, the working Python, and the lessons learned from running it on a real project.

These skills were extracted from production work on *Catalysis*, a short claymation film, where the goal is keeping the human artist in the creative seat while an AI agent handles the mechanical work: scene scaffolding, rig surgery, headless rendering, assembly. The skills are written so that either a human artist or an AI agent following the document can reproduce the result.

## How to use

**As reference documentation.** Read the skill, follow the phases manually in Blender. The CI (check-in) points tell you when to pause and verify before moving forward. The Python snippets are copy-paste runnable in Blender's scripting workspace.

**With an AI agent.** Point a Claude / Cursor / similar agent at a skill document and ask it to execute the workflow on your scene. The skill is structured so the agent knows exactly where to stop and present results back to you (the artist) for green-light. The "Top principle — non-destructive" sections give the agent strict safety rules so your source assets never get modified by accident.

## Skills

| # | Skill | Version | Status | Summary |
|---|---|---|---|---|
| 01 | [Character Disassembly](skills/01_character_disassembly.md) | 1.0.0 | ✅ Stable | Build standalone severable body parts (hand, ear, fingertip) from a fully-rigged character. Independent mesh + trimmed armature per part. Source character stays untouched. |
| 02 | [Render & Assembly](skills/02_render_and_assembly.md) | 2.4.0 | ✅ Stable | Sequential headless rendering with mid-render Haiku vision verification, per-scene abort, pass-isolated output folders, and VSE assembly into final video. |
| 03 | [Body Part Swap Setup](skills/03_body_part_swap_setup.md) | 1.0.0 | ✅ Stable | Companion to Skill 01. Append the body parts library into scene files and keyframe a clean visibility swap between intact and severed states. Documents the shared-action bug and a Blender 5.1 save-crash workaround. |

## Repo conventions

**Skill numbering.** Skills are numbered in canonical order (`01_*`, `02_*`, …). The number is the file name and the document title's prefix. Numbers are stable — a skill never gets renumbered once published.

**Versioning per skill.** Each skill carries its own semver at the top, independent of repo versions. Skill version increments when the workflow itself changes; copy-edits and clarifications don't bump the version.

**Repo versioning.** The repo has its own version in `CHANGELOG.md` — bumped whenever a skill is added, removed, or updated.

**Stop protocols.** Every skill has a "Stop protocols" section listing the formal artist check-in points (CI-1, CI-2, …). These are *hard stops* in the workflow — the agent (or the human running through it) must pause and get explicit confirmation before continuing past each one.

**Non-destructive default.** Every skill that touches source assets follows the same rule: source files are never modified, anything cut goes to a `_junk` collection instead of being deleted, and snapshot saves happen between every destructive step. This is the highest-priority constraint, called out explicitly at the top of any skill where it applies.

**Show-don't-tell prompting.** Skills describe operations mechanically (what to select, what to delete, what to verify). They do not describe intent or effect ("make it look natural"). The artist owns creative judgment; the skill owns mechanical correctness.

## Companion repo

The story-side companion (Robert McKee analysis pipeline, FigJam beat board, scene scaffolding) lives at [TrevorHumble/story-pipeline](https://github.com/TrevorHumble/story-pipeline). Together the two repos cover end-to-end pre-production-to-render for indie animated short film work.

## Contributing

Skills here are extracted from real production work — if you've solved a hairy Blender problem and want to add a skill, the format is: one Markdown file per skill, numbered, with the sections in any existing skill as a template. Pull requests welcome. The bar is *production-tested* — a skill should be one you've actually run on a real project, not a theoretical workflow.

## License

[MIT](LICENSE) © 2026 Trevor Humble
