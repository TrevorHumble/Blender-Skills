# Body Part Swap Setup — Appending a Body Parts Library into Scenes

> **v1.0.0 (2026-05-12):** First version. Companion skill to `01_character_disassembly.md`. Covers how to take a pre-built body parts library (the output of skill 01) and wire it into scene files with visibility keyframes that flip a character between intact and severed states.

## Purpose

Skill 01 builds the body parts as standalone severable assets. This skill is the second half — getting those assets *into* scene files cleanly, organizing them so the artist can toggle the severance moment with a single keyframe edit, and avoiding the data-collision gotchas that happen when appending a Florence-like library into a scene that already contains a Florence-like character.

After this skill runs on a scene file, the artist can scrub the timeline and see frame 1 = intact character, frame 2 = severed state (with both the source mesh hidden and the severed piece visible). The artist drags the frame-2 keyframes to the actual severance moment in their animation.

## Scope and what is deliberately deferred

**Included:**
- Pre-prefix the body parts library with a unique prefix (`fbp_`) so nothing collides on append
- Organize the library into a single parent collection with swap-pair sub-collections (one per severance event)
- Headless append the parent collection into a scene file
- Exclude (via LayerCollection) the scene's existing character + out-of-scope swap collections
- Insert `hide_viewport` + `hide_render` keyframes with CONSTANT interpolation at frames 1 and 2
- Detach severable rigs from any shared Action before keyframing (critical bug avoided here)

**Deferred to other work:**
- Choosing the actual severance frame number — the artist drags the frame-2 keys to the right frame
- Animating the severance choreography (hand falling, ear bouncing, etc.)
- Per-scene visual cleanup (positioning the severed piece at the correct anatomical location)
- The artist's primary animation work (poses, camera, timing)

## Inputs

- A scene `.blend` file with the character already present in some form (typically appended via a separate character pipeline)
- A pre-built body parts library `.blend` file (the output of skill 01) with everything in it `fbp_`-prefixed and organized under one parent collection
- A small JSON config naming which source mesh to hide, which swap collection to show, and which collections are out of scope for this scene

## Stop protocols (artist check-ins)

| Check-in | When | What's being confirmed |
|---|---|---|
| **CI-1: Library prep** | Before any scene work | The body parts library is fully `fbp_`-prefixed (objects, mesh data, armature data, materials, action, image), organized under one parent collection with swap-pair sub-collections. No name conflicts will exist on append. |
| **CI-2: Pilot one scene** | After running on the first scene | The artist opens the scene in the GUI, scrubs frame 1 → frame 2, confirms the swap flips cleanly and the primary rig is still selectable. |
| **CI-3: Per-scene verification** | After running on remaining scenes | Same as CI-2 but for each subsequent scene. |

## Top principle — non-destructive

- **Source scene `.blend` files are never modified.** Always copy them to a working folder (e.g. `_swap_drafts_v3/`) first and apply changes there.
- The scene's existing character collection is **excluded** (LayerCollection-level), not deleted. The artist can re-enable it later if they want.
- All backup files retained.

## The library structure (assumed input)

```
fbp_Florence_BodyParts/                ← single parent collection
├── fbp_Default/                       ← always-on body parts + primary rig
│   ├── fbp_char_grp, fbp_rig
│   ├── fbp_Body/   (Head, Hands, Shirt, Pants, etc.)
│   ├── fbp_Hair/
│   ├── fbp_Face/
│   └── fbp_ControlShapes/
├── fbp_HandR_Swap/                    ← swap-in when R hand severs
│   ├── fbp_Hands_NoHandR (alt source mesh — replaces fbp_Hands)
│   ├── fbp_Hand_R       (severed piece)
│   └── fbp_rig_HandR    (trimmed rig for the severed piece)
├── fbp_EarL_Swap/                     ← swap-in when L ear severs
│   ├── fbp_Head_NoEarL
│   ├── fbp_Ear_L
│   └── fbp_rig_EarL
└── fbp_FingertipR_Swap/               ← swap-in when R fingertip severs
    ├── fbp_Hands_NoFingertipR
    ├── fbp_Fingertip_R_Index
    └── fbp_rig_FingertipRIndex
```

## Workflow (per scene)

For each scene that needs a severance setup:

1. **Copy the source scene** to a working folder (don't touch the original).
2. **Append `fbp_Florence_BodyParts`** from the body parts library via `bpy.data.libraries.load()` with `link=False`. This brings everything in as one bundle.
3. **Exclude the scene's existing character collection** via LayerCollection (`lc.exclude = True`). It's preserved in the file, just not in the active view layer.
4. **Exclude the out-of-scope swap collections** (the two swaps that don't apply to this scene). Same LayerCollection mechanism.
5. **Clear shared actions** on the severable rig in the active swap collection (see "The shared-action bug" below).
6. **Insert visibility keyframes** for the source mesh + each object in the active swap collection.

### Keyframe pattern

```
Source mesh (e.g. fbp_Hands):
  frame 1: hide_viewport = False, hide_render = False    (visible — intact state)
  frame 2: hide_viewport = True,  hide_render = True     (hidden — severed state)

Each object in active swap collection (alt mesh, severed piece, severed rig):
  frame 1: hide_viewport = True,  hide_render = True     (hidden — not yet severed)
  frame 2: hide_viewport = False, hide_render = False    (visible — severance moment)

Primary rig (fbp_rig): no keyframes. Stays visible and selectable at both frames.
```

All keyframes use **CONSTANT interpolation** so visibility flips cleanly at frame 2 instead of fading. Set `bpy.context.preferences.edit.keyframe_new_interpolation_type = 'CONSTANT'` before the keyframe inserts.

## The shared-action bug

**Symptom:** keyframing `fbp_rig_EarL.hide_viewport` also hides `fbp_rig` (the primary armature). The artist loses access to Florence's main rig at frame 1.

**Cause:** when you duplicate an armature in Blender (which is how the trimmed rigs `fbp_rig_HandR`, `fbp_rig_EarL`, `fbp_rig_FingertipRIndex` were created from the source `fbp_rig`), the new armature shares the source's `animation_data.action`. Any keyframe inserted on the duplicate goes into the shared Action, which then drives the source too.

**Fix:** before keyframing a severable rig, clear its action so a new one is created:

```python
if obj.animation_data and obj.animation_data.action:
    obj.animation_data.action = None
# Then keyframe — Blender creates a fresh, dedicated action.
obj.keyframe_insert(data_path='hide_viewport', frame=1)
```

This applies to **all severable rigs** that came from duplicating the source rig.

## The save-crash workaround

**Symptom on Blender 5.1:** running multiple `keyframe_insert()` calls on different objects in a single Blender invocation, then `bpy.ops.wm.save_mainfile()`, sometimes triggers `EXCEPTION_ACCESS_VIOLATION` during save. Address: `0x00007FF...02696`. Affects complex scenes with hundreds of objects.

**Cause:** unclear — likely a Blender 5.1 bug with the new Layered Actions system under load.

**Workaround:** do one `keyframe_insert` target per Blender invocation. Trigger Blender five separate times (one per object being keyframed) instead of doing them all in a single batch. Each invocation: open file, keyframe one object, save, quit. Each takes ~3 seconds. Tedious but reliable.

Pseudocode for the calling shell script:

```bash
for OBJ in source_mesh alt_mesh severed_mesh severed_rig; do
    blender --background --factory-startup scene.blend --python-expr "
import bpy
obj = bpy.data.objects['$OBJ']
obj.hide_viewport = ...
obj.keyframe_insert(data_path='hide_viewport', frame=1)
# (4 keyframe_insert calls — viewport+render × frame 1+2 — per object)
bpy.ops.wm.save_mainfile()
"
done
```

Always use `--factory-startup` to skip addons (some addons access animation_data during init and can compound this bug).

## Per-scene config (the JSON)

Each scene needs a tiny config object naming the swap mapping:

```json
{
  "hide": ["fbp_Hands"],
  "swap": "fbp_HandR_Swap",
  "exclude": ["fbp_FingertipR_Swap", "fbp_EarL_Swap"]
}
```

| Field | Meaning |
|---|---|
| `hide` | Source mesh(es) that get keyframed to hide on severance |
| `swap` | The swap collection whose contents get keyframed to show on severance |
| `exclude` | Out-of-scope swap collections to exclude entirely (LayerCollection) |

## Output

After the workflow runs on a scene, the saved `.blend` contains:

- Scene's original character collection — preserved, but **excluded** from view layer
- `fbp_Florence_BodyParts` collection — appended in full
- Two of the three swap collections — **excluded** (out of scope for this scene)
- One swap collection — active, with visibility keyframes on its contents
- Source mesh — keyframed to flip from visible@1 to hidden@2
- Primary rig `fbp_rig` — accessible, no visibility keyframes

The artist's next steps:
1. Open the file in GUI
2. Pose the primary rig as needed
3. Drag the frame-2 keyframes (on the source mesh + active swap collection contents) to the actual severance frame
4. Position the severed piece at the correct anatomical location at the severance moment (may need additional keyframes for the falling animation)

## Lessons captured (Florence pilot, 2026-05-11/12)

1. **Pre-prefix the entire library** (objects, mesh data, armature data, materials, action, image) before appending — meant no `.001` dedupes on append. Worth ~30 minutes of prep work; saved hours of debugging.
2. **Append the parent collection, not the asset sub-collections individually** — Blender follows parent/modifier references and pulls in everything needed as one bundle. Appending pieces individually creates orphan reference resolution issues.
3. **Use `lc.exclude = True`, not just `lc.hide_viewport`** — exclude removes the collection from the active view layer entirely. Hide just masks it visually; objects still affect dependencies.
4. **The shared-action bug is silent but devastating** — duplicated armatures share their source's Action, so visibility keyframes on a duplicate also affect the source. Always clear `obj.animation_data.action = None` before keyframing.
5. **One keyframe target per Blender invocation, with `--factory-startup`** — works around the Blender 5.1 save-crash on complex scenes.
6. **The severance frame is frame 2 as a placeholder** — the artist drags it to the real frame in the dope sheet. Don't try to be clever and predict the severance moment in the script.

## What this skill does NOT do

- It does not modify source scene files (only working copies in a dedicated folder).
- It does not pose or animate anything. The artist owns all creative work.
- It does not position the severed piece — the piece appears at its library-file rest position. The artist places it.
- It does not synchronize multiple severance events within a single scene (e.g. fever-dream montage). Each scene gets one swap pair active.

## Companion files in this workflow

- `append_fbp.py` — appends `fbp_Florence_BodyParts` from library, reports new datablocks
- `apply_swap.py` — applies the JSON config (excludes + keyframes). Note: due to the save-crash, this is typically called multiple times instead of once
- `inspect_swap.py` — read-only inspection of the scene's post-swap state
