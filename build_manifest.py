#!/usr/bin/env python3
"""build_manifest.py — Scan tours/ directory and rebuild manifest.json.

Usage:
    python3 build_manifest.py          # Update manifest.json
    python3 build_manifest.py --check   # Just check, don't overwrite
"""

import json, os, sys
from pathlib import Path

DIR = Path(__file__).resolve().parent
TOURS_DIR = DIR / "tours"
MANIFEST = TOURS_DIR / "manifest.json"

def scan_tours():
    """Return sorted list of tour IDs from tours/*.json (excluding manifest)."""
    tours = []
    for f in sorted(TOURS_DIR.glob("*.json")):
        if f.name == "manifest.json":
            continue
        try:
            data = json.loads(f.read_text())
            tid = data.get("id", f.stem)
            tours.append(tid)
        except (json.JSONDecodeError, IOError) as e:
            print(f"  ⚠ Skip {f.name}: {e}", file=sys.stderr)
    return tours

def build(check_only=False):
    if not TOURS_DIR.exists():
        print("❌ tours/ directory not found")
        return False

    tours = scan_tours()

    if not tours:
        # Write empty manifest
        if not check_only:
            MANIFEST.write_text("[]\n")
        print("ℹ️  No tours found. Manifest cleared.")
        return True

    if check_only:
        print(f"ℹ️  Would write {len(tours)} tours to manifest.json")
        for t in tours:
            print(f"   - {t}")
        return True

    MANIFEST.write_text(json.dumps(tours, indent=2) + "\n")
    print(f"✅ Manifest updated: {len(tours)} tour(s)")
    for t in tours:
        print(f"   - {t}")
    return True

def main():
    check_only = "--check" in sys.argv
    ok = build(check_only=check_only)
    sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()