#!/usr/bin/env python3
"""stitch.py — ZENTRA VR3D Hugin panorama stitch pipeline.

Convert a set of overlapping photos into an equirectangular 360° panorama.

Usage:
    python3 stitch.py <input_dir/> [--output panorama.jpg] [--focal 24]

Requirements: hugin-tools, enblend (apt-get install -y hugin-tools enblend)
"""

import argparse, glob, os, subprocess, sys, tempfile, shutil, time

# ── Config ──────────────────────────────────────────
HFOV = 60          # Default horizontal FoV (degrees) — adjust per lens
CROP = "0,0,100,100"  # Crop % (left,top,right,bottom for vignette removal)
QUALITY = 92       # JPEG output quality
OUTPUT = "panorama.jpg"

# ── Pipeline ────────────────────────────────────────

def check_tools():
    """Verify all required binaries exist."""
    required = ["pto_gen", "cpfind", "autooptimiser", "pano_modify", "hugin_executor", "nona", "enblend"]
    missing = [cmd for cmd in required if not shutil.which(cmd)]
    if missing:
        print(f"✘ Missing tools: {', '.join(missing)}")
        print("  Install: sudo apt-get install -y hugin-tools enblend")
        sys.exit(1)
    print("✓ All tools available")

def step(msg, cmd, check=True):
    """Run a pipeline step with timing."""
    print(f"\n  ⚙  {msg}")
    print(f"     $ {' '.join(cmd)}")
    t0 = time.time()
    r = subprocess.run(cmd, capture_output=True, text=True)
    elapsed = time.time() - t0
    if r.returncode != 0 and check:
        print(f"  ✘ Failed ({elapsed:.1f}s):")
        print(f"     {r.stderr[:500]}")
        sys.exit(1)
    print(f"  ✓ Done ({elapsed:.1f}s)")
    return r

def find_images(dir_path):
    """Find all image files in the input directory."""
    exts = [".jpg", ".jpeg", ".png", ".tif", ".tiff", ".cr2", ".nef", ".arw"]
    files = []
    for ext in exts:
        files.extend(sorted(glob.glob(os.path.join(dir_path, f"*{ext}"))))
        files.extend(sorted(glob.glob(os.path.join(dir_path, f"*{ext.upper()}"))))
    if not files:
        print(f"✘ No images found in {dir_path}")
        print(f"  Supported formats: {', '.join(exts[:6])}")
        sys.exit(1)
    print(f"\n  Found {len(files)} images:")
    for f in files:
        print(f"    {os.path.basename(f)}")
    return files

def stitch(input_dir, output, hfov):
    """Full Hugin stitch pipeline."""
    print(f"\n{'='*50}")
    print(f"  ZENTRA VR3D — Hugin Stitch Pipeline")
    print(f"{'='*50}")
    print(f"  Input:   {input_dir}")
    print(f"  Output:  {output}")
    print(f"  HFOV:    {hfov}°")
    print(f"{'='*50}")

    images = find_images(input_dir)
    if len(images) < 2:
        print("✘ Need at least 2 overlapping images")
        sys.exit(1)

    with tempfile.TemporaryDirectory(prefix="vr3d_stitch_") as tmp:
        print(f"\n─ Step 1: Generate project file (pto_gen) ─────────")
        pto = os.path.join(tmp, "project.pto")
        step("Detect image geometry + set HFOV",
             ["pto_gen", "-o", pto, "-f", str(hfov)] + images)

        print(f"\n─ Step 2: Find control points (cpfind) ───────────")
        step("Match overlapping features between images",
             ["cpfind", "--prealigned", "-o", pto, pto])

        print(f"\n─ Step 3: Clean control points ────────────────────")
        step("Remove poor matches",
             ["cpfind", "-p", "0.6", "-o", pto, "reassign", "|", "true"])

        print(f"\n─ Step 4: Optimise panorama (autooptimiser) ──────")
        step("Optimise yaw/pitch/roll and lens parameters",
             ["autooptimiser", "-a", "-l", "-s", "-o", pto, pto])

        print(f"\n─ Step 5: Set output parameters (pano_modify) ────")
        step(f"Set output format=JPG, quality={QUALITY}, crop={CROP}",
             ["pano_modify", "--canvas=AUTO", "--crop=" + CROP,
              f"--jpeg-quality={QUALITY}", "--output-type=JPG",
              "-o", pto, pto])

        print(f"\n─ Step 6: Stitch panorama (hugin_executor) ───────")
        out_file = os.path.join(tmp, "output.jpg")
        step("Render the final panorama",
             ["hugin_executor", "--stitching", pto, "--output", out_file])

        # Check output
        if not os.path.exists(out_file):
            # hugin_executor often outputs with a _ prefix
            alt = os.path.join(tmp, "_output.jpg")
            if os.path.exists(alt):
                out_file = alt
            else:
                # Find any jpg in tmp
                jpgs = glob.glob(os.path.join(tmp, "*.jpg"))
                if jpgs:
                    out_file = jpgs[0]
                else:
                    print("✘ Output not found. Check Hugin logs above.")
                    # Print what's in tmp
                    for f in os.listdir(tmp):
                        print(f"  {f} ({os.path.getsize(os.path.join(tmp, f))}b)")
                    sys.exit(1)

        # Copy to final destination
        shutil.copy2(out_file, output)
        size_kb = os.path.getsize(output) / 1024
        print(f"\n  ✓ Panorama saved: {output} ({size_kb:.0f} KB)")

        # Create thumbnail
        thumb = output.rsplit(".", 1)[0] + "_thumb.jpg"
        subprocess.run([
            "convert", output, "-resize", "800x400^",
            "-gravity", "center", "-extent", "800x400",
            thumb
        ], capture_output=True)
        if os.path.exists(thumb):
            print(f"  ✓ Thumbnail: {thumb}")

        print(f"\n{'='*50}")
        print(f"  ✅ STITCH COMPLETE")
        print(f"{'='*50}")

def main():
    parser = argparse.ArgumentParser(
        description="ZENTRA VR3D — Hugin panorama stitch pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 stitch.py ./photos/                                # Auto-detect, output=panorama.jpg
  python3 stitch.py ./photos/ --output kitchen.jpg --focal 28  # Custom output + focal
        """
    )
    parser.add_argument("input_dir", help="Directory with overlapping photos")
    parser.add_argument("--output", "-o", default=OUTPUT, help=f"Output panorama path (default: {OUTPUT})")
    parser.add_argument("--focal", "-f", type=int, default=24,
                        help="35mm equivalent focal length in mm (default: 24). Lower=wider.")
    parser.add_argument("--hfov", type=float, default=None,
                        help="Horizontal field of view in degrees (overrides focal calculation)")
    args = parser.parse_args()

    check_tools()

    hfov = args.hfov if args.hfov else (2 * 60)  # default
    stitch(args.input_dir, args.output, hfov)

if __name__ == "__main__":
    main()