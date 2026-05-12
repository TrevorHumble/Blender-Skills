# Character Disassembly — Building Severable Body Parts

> **v1.0.0 (2026-05-11):** First version. Workflow proven on Florence's right hand for the *Catalysis* short film, where script beats call for body parts to detach on screen (fingertip in 5.3 Black Void, hand in 5.4 Ballroom, ear in 5.5 London Rain, full disassembly in 5.8 Apartment Ending).

## Purpose

Take a fully-rigged character (Auto-Rig Pro or similar) and build a library of **standalone severable body parts** — each a self-contained mesh + independent armature that can be appended into a scene and animated as a free-floating piece. The original character remains completely untouched; severability is achieved by *not including* a part's collection in a scene rather than by destructively cutting the character apart.

A severable part:
- has only its own geometry (e.g. wrist-down for `Hand_R`)
- has its own independent armature (a trimmed duplicate of the source rig — no shared bones or data)
- has a new `Root_<Part>` bone at the break point as the worldspace control
- can be posed independently of the original character (verified via bbox diff under both rigs)
- shares materials with the source

## Scope and what is deliberately deferred

**Included:**
- Inventory of vertex groups on the source mesh per body region
- Duplication of mesh and rig as independent assets
- Aggressive trim of the duplicated rig (delete bones not in the part's chain)
- Cleanup of constraints and drivers that reference dropped bones
- Addition of a new `Root_<Part>` bone for worldspace placement
- Independence verification (pose source → part doesn't move; pose part → source doesn't move)
- Save-snapshot pattern between every destructive step

**Deferred to other work:**
- **Cutting the source character.** We do not modify the source mesh or source rig. To make a character appear "missing" a body part on screen, the scene simply does not include the corresponding part collection, OR a frame-keyed mask modifier on the source mesh hides those verts. Mask modifier is a separate downstream task.
- **Gum patches / stump caps.** Decorative meshes parented at the break point are modeled separately and appended alongside the body part.
- **Animation of the severance moment.** Keyframed choreography (hand falling, bouncing on the floor) is per-scene animation work — not part of building the asset.

## Inputs

- Source character `.blend` file with:
  - A unified armature (typical of Auto-Rig Pro — `rig` object with hundreds of bones, drivers, constraints)
  - Region meshes parented to that armature (`Hands`, `Head`, `Shirt`, etc.) with clean vertex groups using `.l` / `.r` naming and `c_*` controller naming conventions
- Body parts the script calls for (typically 3-8 per character)
- An empty working `.blend` file (or a `Save-As` of the source) where the parts library will live

## Stop protocols (formal artist check-ins)

This skill has **three required check-ins** with the artist. Each is a hard stop.

| Check-in | When | What's being confirmed |
|---|---|---|
| **CI-1: Parts list lock** | Before any extraction | The exact list of severable parts is locked. For each part: which break point (wrist, elbow, neck, etc.), which side (L/R), any naming preferences. |
| **CI-2: Keep-set review** | Before bone deletion in the trimmed rig | The list of bones to KEEP in the trimmed rig is shown to the artist as a categorized list (deform / controllers / helpers). The artist green-lights or curates. |
| **CI-3: Pose-test review** | After trim, before saving final | The artist watches a pose test (rotate `Root_<Part>` → whole part moves; pose a per-segment control → only that segment moves) and confirms the rig is fit for the scenes it needs to support. |

## Top principle — non-destructive

**Never delete or destructively modify anything on the source.** This is the highest-priority rule of the workflow:

- Source meshes (`Hands`, `Head`, etc.) are never edited.
- Source rig (`rig`) is never modified, never has bones removed.
- Source vertex groups are never pruned.
- All work happens on **independent copies** (`mesh.copy()` AND `data.copy()`, `armature.copy()` AND `data.copy()`).
- Anything cut/trimmed from a copy belongs in a `_junk` collection (hidden, but preserved) rather than deleted.
- Backup snapshots saved between every destructive step. Filename pattern: `<file>.PRE-PILOT.blend`, `<file>.SNAPSHOT-N.blend`.

If the artist asks you to "clean up" by deleting unused objects, **move them to `_junk` instead**.

## Architecture note — independent data, not shared

A severable body part needs its own armature **data**, not just its own armature **object**. This matters because:

- An armature object's `pose` is per-object, but the bone structure (rest positions, parents, constraints, drivers) lives on the armature **data**. Trimming bones from data trims them for everyone who shares it.
- If two parts shared one data block and we trimmed it for `Hand_R`, `Hand_L` would lose those bones too.
- The right pattern is `obj.copy()` then `obj.data = obj.data.copy()`. Both calls are needed.

Same goes for mesh data — `obj.copy()` alone gives you a duplicate object that points to the SAME mesh; edits to the duplicate's verts will appear on the source. Always also `obj.data = obj.data.copy()`.

## The eight phases

### Phase A — Pre-flight & safety

1. **Save backup** before any work: `bpy.ops.wm.save_as_mainfile(filepath=<PRE-PILOT_path>, copy=True)`.
2. **Inventory the source mesh's vertex groups** for the target region. Identify:
   - The "keep" groups (e.g. `hand.r`, all `.r` finger groups for `Hand_R`)
   - The "trim out" groups at the break point (e.g. `forearm_stretch.r`, `forearm_twist.r`)
3. **Inventory the source rig's bones** in the relevant chain. List the deform bones, FK controllers, IK controllers, and any `_rot` / `_bend_all` helper bones for fingers.
4. **Save snapshot**.

### Phase B — Mesh duplicate + trim

1. **Duplicate** the source region mesh:
   ```python
   src = bpy.data.objects[src_name]
   new_obj = src.copy()
   new_obj.data = src.data.copy()   # CRITICAL: own mesh data
   new_obj.name = part_name
   new_obj.data.name = part_name
   coll.objects.link(new_obj)
   ```
2. **Trim opposite-side verts** if the source mesh contains both L and R:
   ```python
   delete_suffix = '.l' if side == 'r' else '.r'
   delete_vg_indices = {vg.index for vg in new_obj.vertex_groups
                        if vg.name.endswith(delete_suffix)}
   verts_to_delete = [v.index for v in new_obj.data.vertices
                      if any(g.group in delete_vg_indices and g.weight >= 0.1
                             for g in v.groups)]
   # bmesh delete
   ```
3. **Trim past-the-break verts** (e.g. forearm verts on `Hand_R`):
   - Use **threshold 0.5** here (not 0.1). At 0.5 we keep verts that are mostly hand but slightly weighted to forearm — clean wrist line, no jagged edge.
4. **Prune unused vertex groups** from the new mesh (the L-side groups, the forearm groups). Cosmetic but clean.
5. **Visual check** — isolate the part in viewport, screenshot, confirm shape is right.
6. **Save snapshot**.

### Phase C — Rig duplicate (untrimmed first)

1. **Duplicate the source rig** with independent data:
   ```python
   src_rig = bpy.data.objects['rig']
   new_rig = src_rig.copy()
   new_rig.data = src_rig.data.copy()
   new_rig.name = f'rig_{part_name}'
   new_rig.data.name = f'rig_{part_name}'
   ```
2. **Link to the part's asset collection** (alongside the trimmed mesh).
3. **Don't trim yet.** Verify the untrimmed duplicate works as a parallel rig first. This isolates "did the duplicate succeed" from "did the trim break things."
4. **Save snapshot**.

### Phase D — Rebind mesh to new rig

1. **Re-parent** the trimmed mesh to the new rig (preserve transform):
   ```python
   mat = mesh_obj.matrix_world.copy()
   mesh_obj.parent = new_rig
   mesh_obj.matrix_world = mat
   ```
2. **Point the Armature modifier** at the new rig:
   ```python
   for mod in mesh_obj.modifiers:
       if mod.type == 'ARMATURE':
           mod.object = new_rig
   ```
3. **Independence test (both directions):**
   - Pose a bone in the **source** rig → measure mesh bbox displacement → must be ~0.
   - Pose the equivalent bone in the **new** rig → measure displacement → must be large (~0.05m+ for a small pose, more for a big one).
4. **Save snapshot**.

### Phase E — Build the keep-set

Two strategies for what to keep. Both have been tested:

**Strategy 1 — graph traversal (conservative, ~13% of bones).** Walks parent chains and constraint/driver targets until stable. Keeps the full arm chain + spine root + their controllers. IK works on the trimmed rig. Result: ~77 bones for a hand part.

**Strategy 2 — aggressive (recommended for severable parts, ~8% of bones).** Keeps ONLY the part's own deform bones, helper bones, and FK controllers. Drops IK chain, drops the arm/shoulder/spine back-chain entirely. Adds a new `Root_<Part>` bone at the break point. Result: ~48 bones for a hand part.

For severable body parts that move freely in worldspace (a hand on the floor, a fingertip falling), Strategy 2 is the right call — there's no body for IK to "reach back" through, so IK has no value. FK posing of fingers is what the artist needs, plus `Root_<Part>` for worldspace placement.

**Strategy 2 keep-set for a hand (concrete example):**
- Deform: `hand.r`, `index1.r` `middle1.r` `ring1.r` `pinky1.r` `thumb1.r` (6)
- Helpers: `<finger>1_rot.r`, `<finger>2_rot.r`, `<finger>3_rot.r`, `<finger>_bend_all.r` × 5 fingers (20)
- Controllers: `c_hand_fk.r`, `c_<finger>1.r`, `c_<finger>1_base.r`, `c_<finger>2.r`, `c_<finger>3.r` × 5 (21)
- New: `Root_<Part>` (1)
- **Total: ~48 bones**

CI-2 stops here and presents this list to the artist before any deletion.

### Phase F — Trim the rig

1. **Clean external constraints first.** For each kept pose bone, iterate `pb.constraints`. If a constraint's `subtarget` is outside the keep-set, remove the constraint. (For Florence's `Hand_R`, this was 3 constraints — `hand.r`'s Copy Rotation/Scale from `c_hand_ik.r` and Copy Location from `forearm_ik.r`.)
2. **Clean external drivers.** Walk `rig.animation_data.drivers`. For each driver on a kept bone, check every variable target. If a target is outside the keep-set, remove the driver via `rig.driver_remove(data_path, array_index)`. (Florence: 5 drivers removed, all referencing `c_ikfk_arm.r` or `c_autostretchr`.)
3. **Add `Root_<Part>` bone** in Edit mode. Place at the break point:
   - Head = head of the topmost deform bone (e.g. wrist median for `Hand_R`)
   - Tail = head + 0.1m along a useful axis (`+Z` is fine for a hand)
4. **Reparent orphaned kept bones** to `Root_<Part>`:
   - For each kept bone, check if its `parent` is in the keep-set
   - If not, set `parent = Root_<Part>`, `use_connect = False`
5. **Delete bones** not in the keep-set:
   ```python
   bpy.ops.object.mode_set(mode='EDIT')
   for b in [b for b in rig.data.edit_bones if b.name not in keep_set]:
       rig.data.edit_bones.remove(b)
   bpy.ops.object.mode_set(mode='OBJECT')
   ```
6. **Console check.** Look for red driver/constraint warnings. If anything goes red, Ctrl-Z to the snapshot and consult the artist.
7. **Save snapshot**.

### Phase G — Pose-test verification

Test multiple controls on multiple axes — some controls die after the trim, and you need to know which ones.

```python
def get_bbox(obj):
    deps = bpy.context.evaluated_depsgraph_get()
    eo = obj.evaluated_get(deps)
    me = eo.to_mesh()
    xs=[v.co.x for v in me.vertices]; ys=[v.co.y for v in me.vertices]; zs=[v.co.z for v in me.vertices]
    bb=(min(xs),max(xs),min(ys),max(ys),min(zs),max(zs))
    eo.to_mesh_clear()
    return bb

# Test each control on X/Y/Z, report bbox displacement
for ctrl in test_controls:
    for axis in [Vector((1,0,0)), Vector((0,1,0)), Vector((0,0,1))]:
        pb.rotation_quaternion = Quaternion(axis, radians(60))
        depsgraph_update()
        bbox_p = get_bbox(mesh)
        delta = max(abs(bbox_rest[i]-bbox_p[i]) for i in range(6))
        # ... record
        pb.rotation_quaternion = Quaternion((1,0,0,0))
```

**What "works":** `Root_<Part>` rotates the whole part (largest displacement). Per-finger base controls (`c_*1_base.r`) curl from the knuckle. First-and-second-segment FK controls work on Z axis. (Curl axis for ARP fingers is **Z**, not X.)

**What dies after aggressive trim:**
- Hand-level FK control (`c_hand_fk.r`) becomes orphaned (its children — the FK forearm chain — were deleted). It's harmless dead weight. Move it to `_junk` or leave it.
- Fingertip controls (`c_*3.r`) often die — they depend on driver chains we removed. Animator can curl the first two segments of each finger, not the very tip. For severance scenes this is fine; for hero close-ups of a hand, restore the dependency chain or use Strategy 1 instead.

Present pose-test results to the artist at CI-3.

### Phase H — Document and reuse

1. **Capture the working Python** from B, C, F as a reusable script (per-character, since rig structures differ).
2. **Update the parts manifest** — a JSON mapping each script-named severable part to the source mesh + VG list + keep-set seed:
   ```json
   {
     "Hand_R": {
       "source_mesh": "Hands",
       "side": "r",
       "break_groups": ["forearm_stretch.r", "forearm_twist.r"],
       "break_threshold": 0.5,
       "keep_seed_deform": ["hand.r", "index1.r", "middle1.r", "ring1.r", "pinky1.r", "thumb1.r"],
       "keep_seed_helpers": ["*1_rot.r", "*2_rot.r", "*3_rot.r", "*_bend_all.r"],
       "keep_seed_controls": ["c_hand_fk.r", "c_*1.r", "c_*1_base.r", "c_*2.r", "c_*3.r", "c_thumb1_base.r"]
     }
   }
   ```
3. **Note any rig-specific gotchas** (the dead controls, the curl axis, etc.) so the next artist using a different rig knows what to check.

## Output

After this skill runs successfully for a part `<Part>`, the working `.blend` file contains:

- **Source assets untouched** — original mesh, original rig, original collections, original drivers and constraints.
- **`<Part>_Asset` collection** containing:
  - `<Part>` — the trimmed mesh
  - `rig_<Part>` — the trimmed independent armature with `Root_<Part>` as the top-level transform
- **`_junk` collection (hidden)** containing the full untrimmed rig backup `rig_<Part>_BACKUP_full` and any other safety duplicates.
- **Snapshot files** alongside the working file: `…PRE-PILOT.blend`, `…SNAPSHOT-N.blend`.

The part can now be appended into any scene via `bpy.data.libraries.load()` referencing `<Part>_Asset` by collection name. The scene gets a free-floating, poseable body part bound to its own rig, with no dependency on the source character being present.

## Lessons captured (Florence pilot, 2026-05-11)

1. **Vertex group threshold matters per mesh.** `Hands` had 0 midline overlap so threshold 0.1 was fine. `Pants` had 110 verts weighted to BOTH sides (crotch / midline) — at threshold 0.1 those got deleted from both L and R copies, leaving a hole. Use 0.5 (or position-based assignment) when midline overlap exists.
2. **MCP for pilot, headless for production.** First build of a part type wants viewport screenshots after every step — Auto-Rig Pro behavior is hard to predict and a visual confirmation per phase catches problems early. Once the workflow is captured as a script, subsequent parts of the same type build headless.
3. **Aggressive trim is safe for free-floating parts.** A severed hand doesn't need to "reach back" through a body — IK is dead weight. Strategy 2 (drop the back-chain entirely) is the right default for any part the script depicts as detached.
4. **ARP finger curl is Z axis, not X.** Knee-jerk assumption is X (the "obvious" pivot axis); in ARP it's Z. Always test all three axes per control during pose-test before declaring a control "dead."
5. **`c_*3` controls and `c_hand_fk` will die after aggressive trim.** Acceptable for severance scenes where fingertip-level control isn't needed. For hero closeups, use Strategy 1 or curate the keep-set manually.
6. **Source region collections are NOT cleanup debris.** If the artist has organized source meshes into region collections (e.g. `Lower Half` for pants, `Feet` for slippers+socks), those are deliberate organization — never move them into `_junk` mistaking them for leftover experiments. When in doubt, ask.

## What this skill does NOT do

- It does not animate the severance moment (frame-keyed mesh-mask, the hand falling, etc.).
- It does not model gum patches, stump caps, or any decorative geometry at the break point.
- It does not append parts into scene files — that's done by the per-scene assembly skill using the manifest.
- It does not validate that the part's break geometry "looks right" for camera — that's the artist's call after seeing the part isolated in viewport at the end of Phase B and Phase F.
