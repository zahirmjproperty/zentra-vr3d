#!/usr/bin/env python3
"""Sahkan warna bahan GLB/USDZ dan periksa warna sebenar dalam render."""
import json, struct
import numpy as np
import trimesh
from pathlib import Path

# Laluan relatif kepada lokasi skrip -> boleh dijalankan dari mana-mana.
AKAR = Path(__file__).resolve().parent.parent
from PIL import Image

M = AKAR / "models"
P = AKAR / "preview"

print("=== Warna bahan GLB ===")
for nama in ("bangunan-konsep", "sofa-3-seater"):
    adegan = trimesh.load(str(M / f"{nama}.glb"), force="scene")
    warna = []
    for gk, g in adegan.geometry.items():
        try:
            f = g.visual.material.baseColorFactor
            warna.append(tuple(round(float(x) * 255) for x in f[:3]))
        except Exception as e:
            warna.append(f"<{e}>")
    uniq = sorted(set(w for w in warna if isinstance(w, tuple)))
    print(f"{nama}: {len(adegan.geometry)} primitif, {len(uniq)} warna unik")
    for w in uniq:
        print(f"    rgb{w}")

print("\n=== Warna bahan USDZ (UsdPreviewSurface diffuseColor) ===")
from pxr import Usd, UsdShade
for nama in ("bangunan-konsep", "sofa-3-seater"):
    stage = Usd.Stage.Open(str(M / f"{nama}.usdz"))
    warna = set()
    for prim in stage.Traverse():
        if prim.IsA(UsdShade.Shader):
            sh = UsdShade.Shader(prim)
            inp = sh.GetInput("diffuseColor")
            if inp:
                v = inp.Get()
                if v is not None:
                    warna.add(tuple(round(float(x) * 255) for x in v))
    print(f"{nama}: {len(warna)} warna")
    for w in sorted(warna):
        print(f"    rgb{w}")

print("\n=== Warna sebenar dalam render (piksel) ===")
im = Image.open(P / "bangunan-konsep-zbuffer.png").convert("RGB")
a = np.asarray(im).reshape(-1, 3)
# tapis latar 0.90*255 = 229
bukan = a[(np.abs(a.astype(int) - 229).max(axis=1) > 6)]
print(f"piksel model: {len(bukan)}")
# adakah ada piksel keemasan? (R > G > B, R-B ketara)
emas = bukan[(bukan[:, 0].astype(int) - bukan[:, 2].astype(int) > 22)]
print(f"piksel keemasan (R-B>22): {len(emas)}")
if len(emas):
    print("  purata rgb:", emas.mean(axis=0).round(1))
    print("  maks rgb  :", emas.max(axis=0))
