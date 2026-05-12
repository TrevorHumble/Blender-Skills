"""Assemble all rendered scene sequences into a single Blender VSE timeline.

Usage:
    blender --background --python assemble_vse.py -- /path/to/renders /path/to/output.blend

Steps:
  1. Open a fresh empty .blend
  2. For each scene folder under render_root, find the PNG sequence
  3. Add it as an Image strip to the VSE timeline at the next available frame
  4. Save the .blend as the assembled animatic project

After the script runs, open the saved .blend in Blender, switch to the Video
Editing workspace, scrub through, then File > Render Animation to export the
final cut as MP4.

Folders are processed in alphabetical order — name your scene render folders
so they sort into the correct order (the canonical Act.N-Scene.N convention
sorts naturally).
"""
import bpy
import sys
import os
import glob


def parse_args():
    argv = sys.argv
    if "--" not in argv:
        raise RuntimeError("Pass: -- /path/to/renders /path/to/output.blend")
    args = argv[argv.index("--") + 1:]
    if len(args) < 2:
        raise RuntimeError("Need both render_root and output_blend")
    return args[0], args[1]


def discover_scene_sequences(render_root):
    """Return a sorted list of (scene_label, [frame_paths]) tuples."""
    out = []
    for scene_dir in sorted(os.listdir(render_root)):
        full = os.path.join(render_root, scene_dir)
        if not os.path.isdir(full):
            continue
        frames = sorted(glob.glob(os.path.join(full, "*.png")))
        if frames:
            out.append((scene_dir, frames))
    return out


def main():
    render_root, output_blend = parse_args()

    bpy.ops.wm.read_factory_settings(use_empty=True)

    scene = bpy.context.scene
    scene.sequence_editor_create()
    seq_editor = scene.sequence_editor

    sequences = discover_scene_sequences(render_root)
    print(f"=== Found {len(sequences)} scene folders with frames")

    cursor = 1
    for label, frames in sequences:
        strip = seq_editor.strips.new_image(
            name=label,
            filepath=frames[0],
            channel=1,
            frame_start=cursor,
        )
        for f in frames[1:]:
            strip.elements.append(os.path.basename(f))
        duration = len(frames)
        print(f"  + {label}  frames {cursor}-{cursor + duration - 1}  ({duration} frames)")
        cursor += duration

    scene.frame_start = 1
    scene.frame_end = max(cursor - 1, 1)

    out_dir = os.path.join(os.path.dirname(output_blend), "animatic_out")
    os.makedirs(out_dir, exist_ok=True)
    scene.render.filepath = os.path.join(out_dir, "animatic_")
    # Output format defaults to PNG sequence; user changes to MP4/H.264 in GUI
    # before rendering the final cut. (FFMPEG enum location changed in Blender 5.x;
    # GUI handles this consistently across versions.)
    scene.render.image_settings.file_format = "PNG"

    bpy.ops.wm.save_as_mainfile(filepath=output_blend)
    print(f"=== Saved to {output_blend}")


main()
