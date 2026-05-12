"""Render the currently open scene to a PNG sequence in a per-scene output folder.

Usage:
    blender --background scene.blend --python render_scene.py -- /path/to/output_root

Output structure:
    output_root/
      Act.1-Scene.5-Beach/
        Beach_0001.png
        Beach_0002.png
        ...

Defaults are tuned for animatic speed: half-resolution (50% of scene's
resolution_x/y), EEVEE engine, PNG output. Tune SETTINGS below or override
per scene by editing each .blend's render properties before calling.
"""
import bpy
import sys
import os

# === SETTINGS ===
RESOLUTION_PERCENTAGE = 50  # 50% of scene's resolution_x/y; lower = faster
FRAME_RATE = 24
ENGINE = "BLENDER_EEVEE_NEXT"  # Blender 5.x EEVEE; falls back to BLENDER_EEVEE for 4.x
FILE_FORMAT = "PNG"
# ================


def parse_output_root():
    argv = sys.argv
    if "--" not in argv:
        raise RuntimeError("Pass output root after --, e.g.: -- /path/to/renders")
    args = argv[argv.index("--") + 1:]
    if not args:
        raise RuntimeError("Pass output root after --, e.g.: -- /path/to/renders")
    return args[0]


def scene_label(blend_path):
    """Derive 'Act.1-Scene.5-Beach' from the blend filename, stripping ' - complete' if present."""
    base = os.path.splitext(os.path.basename(blend_path))[0]
    if base.endswith(" - complete"):
        base = base[: -len(" - complete")]
    return base


def main():
    output_root = parse_output_root()
    label = scene_label(bpy.data.filepath)
    out_dir = os.path.join(output_root, label)
    os.makedirs(out_dir, exist_ok=True)

    scene = bpy.context.scene

    try:
        scene.render.engine = ENGINE
    except TypeError:
        scene.render.engine = "BLENDER_EEVEE"

    scene.render.image_settings.file_format = FILE_FORMAT
    scene.render.resolution_percentage = RESOLUTION_PERCENTAGE
    scene.render.fps = FRAME_RATE

    # Output path — Blender appends frame number + extension
    scene.render.filepath = os.path.join(out_dir, label + "_")

    print(f"=== Rendering {label}")
    print(f"=== Frames {scene.frame_start}-{scene.frame_end} -> {out_dir}")
    bpy.ops.render.render(animation=True)
    print(f"=== Done {label}")


main()
