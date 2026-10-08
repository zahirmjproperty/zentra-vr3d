#!/usr/bin/env python3
"""generate_qr.py — Generate QR codes for VR tours.

Usage:
    python3 generate_qr.py tours/armani-a1.json
    python3 generate_qr.py --all                          # All tours
    python3 generate_qr.py tours/armani-a1.json --print     # Print to terminal
    
Output:
    assets/qr/<tour-id>.png — QR code image (1024x1024)
"""

import json, os, sys, argparse
from pathlib import Path

DIR = Path(__file__).resolve().parent
QR_DIR = DIR / "assets" / "qr"
QR_DIR.mkdir(parents=True, exist_ok=True)

BASE_URL = "https://vr3d.zentrapropertygroup.com"

def generate(tour_id: str, tour_path: Path, print_terminal: bool = False) -> bool:
    """Generate QR code for a single tour."""
    try:
        data = json.loads(tour_path.read_text())
    except (json.JSONDecodeError, IOError) as e:
        print(f"  ✘ {tour_id}: {e}", file=sys.stderr)
        return False

    tour_url = f"{BASE_URL}/tour.html?id={tour_id}"
    title = data.get("title", tour_id)

    import qrcode
    qr = qrcode.QRCode(
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=16,
        border=4,
    )
    qr.add_data(tour_url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="#071525", back_color="#ffffff")
    out = QR_DIR / f"{tour_id}.png"
    img.save(out)
    print(f"  ✓ {tour_id:30s} → {out} ({tour_url})")

    if print_terminal:
        try:
            # Also print QR to terminal
            qr_term = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, border=1)
            qr_term.add_data(tour_url)
            qr_term.make(fit=True)
            qr_term.print_ascii(invert=True)
        except:
            pass

    return True

def main():
    parser = argparse.ArgumentParser(description="Generate QR codes for VR tours")
    parser.add_argument("tours", nargs="*", help="Tour JSON files to generate QR for")
    parser.add_argument("--all", "-a", action="store_true", help="Generate for all tours in manifest")
    parser.add_argument("--print", "-p", action="store_true", help="Also print QR to terminal")
    args = parser.parse_args()

    TOURS_DIR = DIR / "tours"
    MANIFEST = TOURS_DIR / "manifest.json"

    if args.all:
        if not MANIFEST.exists():
            print("❌ manifest.json not found. Run build_manifest.py first.")
            return
        tour_ids = json.loads(MANIFEST.read_text())
        files = []
        for tid in tour_ids:
            p = TOURS_DIR / f"{tid}.json"
            if p.exists():
                files.append((tid, p))
    elif args.tours:
        files = []
        for t in args.tours:
            p = Path(t)
            if not p.exists():
                p = DIR / t
            if p.exists():
                files.append((p.stem, p))
            else:
                print(f"  ⚠ Not found: {t}")
    else:
        print("Usage: generate_qr.py tours/armani-a1.json  or  generate_qr.py --all")
        return

    if not files:
        print("No tours to process.")
        return

    print(f"Generating QR codes ({len(files)} tour(s))...")
    ok = sum(1 for tid, fp in files if generate(tid, fp, args.print))
    print(f"\nDone: {ok}/{len(files)} QR codes in {QR_DIR}")

if __name__ == "__main__":
    main()