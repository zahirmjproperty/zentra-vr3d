#!/usr/bin/env python3
"""add_tour.py — Add a new VR tour to Zentra VR3D.

Usage:
    python3 add_tour.py assets/panorama-bilik.jpg \\
        --name "Rumah Idaman" --desc "3-room terrace" \\
        --scene "Living Room" --scene "Kitchen" --scene "Bedroom"

For multiple panoramas (one per scene):
    python3 add_tour.py assets/living.jpg assets/kitchen.jpg assets/bedroom.jpg \\
        --name "Rumah Idaman"

Output:
    - tours/<id>.json — tour data
    - Auto-registers in tour manifest
"""

import hashlib, json, os, sys, argparse
from pathlib import Path

DIR = Path(__file__).resolve().parent
TOURS_DIR = DIR / "tours"
TOURS_DIR.mkdir(exist_ok=True)

def gen_id(name: str) -> str:
    base = name.lower().replace(" ", "-").replace("_", "-")
    base = "".join(c for c in base if c.isalnum() or c == "-")
    # Short hash for uniqueness
    h = hashlib.md5((name + str(os.urandom(4))).encode()).hexdigest()[:6]
    return f"{base[:20]}-{h[:6]}"

def main():
    parser = argparse.ArgumentParser(description="Add a VR tour")
    parser.add_argument("panoramas", nargs="+", help="Panorama image(s), one per scene")
    parser.add_argument("--name", "-n", default="New Tour", help="Property name")
    parser.add_argument("--desc", "-d", default="", help="Short description")
    parser.add_argument("--scene", "-s", nargs="*", help="Scene names (default: auto)")
    parser.add_argument("--id", help="Tour ID (default: auto from name)")
    args = parser.parse_args()

    tour_id = args.id or gen_id(args.name)
    scene_names = args.scene or [f"Scene {i+1}" for i in range(len(args.panoramas))]
    while len(scene_names) < len(args.panoramas):
        scene_names.append(f"Scene {len(scene_names)+1}")

    import datetime
    today = datetime.date.today().isoformat()

    scenes = []
    for i, pano in enumerate(args.panoramas):
        p = pano if pano.startswith("/") else ("/" + pano)
        scenes.append({
            "id": f"scene-{i+1}",
            "title": scene_names[i] if i < len(scene_names) else f"Scene {i+1}",
            "panorama": p,
            "initial": {"pitch": 0, "yaw": 0, "hfov": 100},
            "hotSpots": []
        })

    tour = {
        "id": tour_id,
        "title": args.name,
        "property": args.name,
        "description": args.desc,
        "thumb": args.panoramas[0] if args.panoramas else "",
        "created": today,
        "scenes": scenes
    }

    path = TOURS_DIR / f"{tour_id}.json"
    with open(path, "w") as f:
        json.dump(tour, f, indent=2)
    print(f"✅ Tour created: {path}")
    print(f"   ID: {tour_id}")
    print(f"   URL: /tour.html?id={tour_id}")
    print(f"   Scenes: {len(scenes)}")
    print()
    print("To view: https://vr3d.zentrapropertygroup.com/tour.html?id=" + tour_id)

if __name__ == "__main__":
    main()