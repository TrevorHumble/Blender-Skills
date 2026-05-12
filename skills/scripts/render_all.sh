#!/usr/bin/env bash
# Headless-render every scene in a Draft folder to a per-scene output folder.
# Edit BLENDER, SCRIPT, DRAFT, OUTPUT_ROOT, and the SCENES list for your project.
#
# Usage:
#   bash render_all.sh
#
# The render itself uses scripts/render_scene.py — settings live there.

set -e

BLENDER='/c/Program Files/Blender Foundation/Blender 5.1/blender.exe'
SCRIPT='/path/to/production/scripts/render_scene.py'
DRAFT='/path/to/your/project/Scenes/Draft 2'
OUTPUT_ROOT='/path/to/your/project/renders'

mkdir -p "$OUTPUT_ROOT"

# List scenes in canonical order so logs read top to bottom of the film.
# Include both completed (with " - complete" suffix) and in-progress scenes.
SCENES=(
    "Act.1-Scene.1-Apartment - complete"
    "Act.1-Scene.2-BakedBean - complete"
    "Act.1-Scene.3-Meadow - complete"
    "Act.1-Scene.4-Flight - complete"
    "Act.1-Scene.5-Beach"
    "Act.2-Scene.1-Riverwalk"
    "Act.2-Scene.2-BlackVoid"
    "Act.2-Scene.3-Ballroom"
    "Act.2-Scene.4-ApartmentReturn"
    "Act.2-Scene.5-London"
    "Act.2-Scene.6-FeverDream"
    "Act.2-Scene.7-BarbieBox"
    "Act.2-Scene.8-Swallow"
    "Act.3-Scene.1-ApartmentFinal"
)

for scene in "${SCENES[@]}"; do
    blend="$DRAFT/${scene}.blend"
    if [ ! -f "$blend" ]; then
        echo ">>> SKIP (file missing): $scene"
        continue
    fi
    echo ""
    echo "================================================================"
    echo ">>> $scene"
    echo "================================================================"
    "$BLENDER" --background "$blend" --python "$SCRIPT" -- "$OUTPUT_ROOT" 2>&1 | grep -E "^(===|Append|Fra:)" || true
done

echo ""
echo "All scenes rendered to: $OUTPUT_ROOT"
