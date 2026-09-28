#!/usr/bin/env python3
"""Sahkan model Fasa 0: USDZ boleh dibuka, GLB boleh dibaca, skala & titik asal betul."""
import json
import numpy as np
import trimesh
from pathlib import Path

# Laluan relatif kepada lokasi skrip -> boleh dijalankan dari mana-mana.
AKAR = Path(__file__).resolve().parent.parent
from pxr import Usd, UsdGeom

M = AKAR / "models"

# --- sahkan ketibaan resampling 90 darjah ---
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))

lapor = {}
for nama in ("bangunan-konsep", "sofa-3-seater"):
    glb = M / f"{nama}.glb"
    usdz = M / f"{nama}.usdz"

    # GLB
    adegan = trimesh.load(str(glb), force="scene")
    gelembung = np.vstack([g.bounds for g in adegan.geometry.values()])
    lo, hi = gelembung.min(axis=0), gelembung.max(axis=0)

    # USDZ
    stage = Usd.Stage.Open(str(usdz))
    prim = stage.GetDefaultPrim()
    bbox = UsdGeom.BBoxCache(Usd.TimeCode.Default(), [UsdGeom.Tokens.default_])
    rng = bbox.ComputeWorldBound(prim).ComputeAlignedRange()
    umin, umax = rng.GetMin(), rng.GetMax()

    lapor[nama] = {
        "glb_boleh_dibaca": len(adegan.geometry) > 0,
        "glb_bahagian": len(adegan.geometry),
        "glb_bait": glb.stat().st_size,
        "glb_saiz_m": [round(float(x), 3) for x in (hi - lo)],
        "glb_y_min": round(float(lo[1]), 4),
        "usd_boleh_dibuka": bool(stage),
        "usd_up_axis": str(UsdGeom.GetStageUpAxis(stage)),
        "usd_meters_per_unit": round(float(UsdGeom.GetStageMetersPerUnit(stage)), 4),
        "usd_saiz_m": [round(float(umax[i] - umin[i]), 3) for i in range(3)],
        "usd_y_min": round(float(umin[1]), 4),
        "usd_bait": usdz.stat().st_size,
        "sepadan_dalam_5cm": all(
            abs(float(hi[i] - lo[i]) - float(umax[i] - umin[i])) < 0.05 for i in range(3)),
    }

print(json.dumps(lapor, indent=2, ensure_ascii=False))
