#!/usr/bin/env bash
set -euo pipefail

# build_tour.sh — One-command VR tour build pipeline.
# Usage:
#   ./build_tour.sh ./photos/ --name "No 12 Jalan SS2" --scene "Living Room" --scene "Kitchen"

DIR="$(cd "$(dirname "$0")" && pwd)"
PHOTO_DIR=""
NAME=""
SCENES=()

# Parse args: everything before --name is photo dir, --name and beyond are for add_tour.py
while [[ $# -gt 0 ]]; do
    case "$1" in
        --name|-n|--desc|-d|--scene|-s|--id)
            # Switches to add_tour.py mode
            break
            ;;
        *)
            PHOTO_DIR="$1"
            shift
            ;;
    esac
done

if [ -z "$PHOTO_DIR" ]; then
    echo "Usage: $0 <photo-dir/> --name \"Property Name\" [--scene \"Room 1\"] ..."
    exit 1
fi

# Step 1: Stitch each batch of photos (one subfolder per scene)
echo "━━━ Step 1: Stitch panoramas ━━━"
STITCHED=()
SCENE_INDEX=0

# If photo dir has subdirs, stitch each subdir as a scene
# Otherwise, stitch the whole dir as one scene
HAS_SUBDIRS=0
for d in "$PHOTO_DIR"/*/; do
    if [ -d "$d" ]; then
        HAS_SUBDIRS=1
        break
    fi
done

if [ "$HAS_SUBDIRS" -eq 1 ]; then
    # Each subdirectory = one scene
    for d in "$PHOTO_DIR"/*/; do
        name="$(basename "$d")"
        output="assets/panorama-$(basename "$d" | tr '[:upper:]' '[:lower:]' | tr ' ' '-').jpg"
        echo "  Stitching scene: $name → $output"
        python3 "$DIR/stitch.py" "$d" --output "$output" --quiet 2>/dev/null || {
            echo "  ⚠ Stitch failed for $d, skipping"
            continue
        }
        STITCHED+=("$output")
    done
else
    # Single batch — stitch all photos into one panorama
    output="assets/panorama-$(basename "$PHOTO_DIR" | tr '[:upper:]' '[:lower:]' | tr ' ' '-').jpg"
    echo "  Stitching all photos → $output"
    python3 "$DIR/stitch.py" "$PHOTO_DIR" --output "$output" --quiet 2>/dev/null || {
        echo "  ⚠ Stitch failed, trying direct copy as fallback"
        # Find first jpg and use as-is if stitch fails
        first_img=$(find "$PHOTO_DIR" -maxdepth 1 -name '*.jpg' -o -name '*.jpeg' -o -name '*.png' | head -1)
        if [ -n "$first_img" ]; then
            cp "$first_img" "$output"
            echo "  ✓ Copied $first_img as fallback panorama"
        fi
    }
    STITCHED+=("$output")
fi

if [ ${#STITCHED[@]} -eq 0 ]; then
    echo "❌ No panoramas produced. Check your photos."
    exit 1
fi

# Step 2: Add tour via add_tour.py with remaining args
echo ""
echo "━━━ Step 2: Register tour ━━━"
python3 "$DIR/add_tour.py" "${STITCHED[@]}" "$@"

# Step 3: Rebuild manifest
echo ""
echo "━━━ Step 3: Build manifest ━━━"
python3 "$DIR/build_manifest.py"

# Step 4: Summary
echo ""
echo "━━━ Done ━━━"
echo "Panoramas: ${STITCHED[*]}"
echo "Push to GitHub to publish:"
echo "  cd $DIR && python3 deploy_vr3d.py"
echo "Or wait for the next automatic deploy."