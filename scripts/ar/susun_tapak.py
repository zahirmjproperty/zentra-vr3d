#!/usr/bin/env python3
"""Susun tapak AR Fasa 0 untuk deploy ke repo zentra-vr3d.

Salinan TIDAK sunting: model dibina oleh bina_model.py, kod QR oleh jana_qr.py.
Skrip ini hanya meletakkan fail pada tempat yang betul + semak rujukan silang.
"""
import json
import shutil
import urllib.request
from pathlib import Path

# Laluan relatif kepada lokasi skrip -> boleh dijalankan dari mana-mana.
AKAR = Path(__file__).resolve().parent.parent

AKAR = AKAR
SITE = AKAR / "site"
MODEL = SITE / "models"

# 1. model -> models/projects + models/furniture
(MODEL / "projects").mkdir(parents=True, exist_ok=True)
(MODEL / "furniture").mkdir(parents=True, exist_ok=True)

PETA = {
    "bangunan-konsep": "projects",
    "sofa-3-seater": "furniture",
}
dipindah = []
for nama, sub in PETA.items():
    for ext in ("glb", "usdz"):
        src = AKAR / "models" / f"{nama}.{ext}"
        dst = MODEL / sub / f"{nama}.{ext}"
        shutil.copy2(src, dst)
        dipindah.append((dst.relative_to(SITE).as_posix(), dst.stat().st_size))

# 2. penjejak -> site/assets
(SITE / "assets").mkdir(parents=True, exist_ok=True)
url_trk = "https://raw.githubusercontent.com/zahirmjproperty/zentra-vr3d/main/assets/zvr3d-tracker.js"
dst_trk = SITE / "assets" / "zvr3d-tracker.js"
try:
    with urllib.request.urlopen(url_trk, timeout=45) as r:
        dst_trk.write_bytes(r.read())
    sumber_trk = "repo zentra-vr3d (versi hidup)"
except Exception as e:
    sumber_trk = f"GAGAL: {e}"
    dst_trk.write_text("/* penjejak tidak dapat dimuat */\n", encoding="utf-8")

# 3. semak setiap rujukan fail dalam HTML benar-benar wujud
rujukan, hilang = [], []
for html in sorted(SITE.rglob("*.html")):
    teks = html.read_text(encoding="utf-8")
    import re
    for m in re.finditer(r'(?:src|href)="(\.\.?/[^"#?]+)"', teks):
        p = (html.parent / m.group(1)).resolve()
        rujukan.append((html.name, m.group(1)))
        if not p.exists():
            hilang.append((html.name, m.group(1)))

# 4. semak manifest sepadan dengan fail sebenar
man = json.loads((MODEL / "manifest.json").read_text(encoding="utf-8"))
man_hilang = []
for k, m in man["model"].items():
    for key in ("glb", "usdz"):
        p = (MODEL / m[key].replace("../models/", "")).resolve()
        if not p.exists():
            man_hilang.append((k, key, m[key]))

print(json.dumps({
    "model_disalin": dipindah,
    "penjejak": {"sumber": sumber_trk, "bait": dst_trk.stat().st_size},
    "rujukan_dalam_html": len(rujukan),
    "rujukan_hilang": hilang,
    "manifest_hilang": man_hilang,
    "jumlah_bait_tapak": sum(f.stat().st_size for f in SITE.rglob("*") if f.is_file()),
}, ensure_ascii=False, indent=2))
