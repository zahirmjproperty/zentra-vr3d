#!/usr/bin/env python3
"""
ZENTRA VR3D-AR — Fasa 0
Bina model 3D (GLB + USDZ) dalam unit METER, titik asal di TENGAH PANGKAL.

Prinsip (kajian 28 Sep 2026):
  - 1 unit = 1 meter untuk kedua-dua glTF dan USD
  - Titik asal: x=0, z=0 = tengah tapak; y=0 = aras tanah
  - Y-up untuk kedua-dua format
  - GLB (Android / WebXR / model-viewer) + USDZ (iOS AR Quick Look)

Reka bentuk: satu senarai bahagian (part) dengan warna eksplisit per bahagian.
Dijadualkan ke dalam kumpulan warna -> satu geometri per warna -> satu primitif
glTF per bahan. Tidak bergantung pada andaian material trimesh.
"""
import json, struct, zipfile
from pathlib import Path

import numpy as np
import trimesh

# Laluan relatif kepada lokasi skrip -> boleh dijalankan dari mana-mana sahaja.
# Skrip mesti berada di <akar>/scripts/ supaya model ditulis ke <akar>/models/.
AKAR = Path(__file__).resolve().parent.parent
OUT = AKAR / "models"
OUT.mkdir(parents=True, exist_ok=True)


# ============================================================
# Pembina geometri - senarai (vertices, faces, warna_rgb)
# ============================================================

def _kotak(w, h, d, x, y, z):
    """Kotak berpusat (x,y,z). Pulangkan (vertices, faces)."""
    m = trimesh.creation.box(extents=(w, h, d))
    v = np.asarray(m.vertices, dtype=np.float64) + np.array([x, y, z], dtype=np.float64)
    return v, np.asarray(m.faces, dtype=np.int64)


def _silinder(r, h, x, y, z, seksyen=16):
    """Silinder PAKSI MENEGAK (Y). trimesh mencipta paksi Z secara lalai — putar 90 darjah."""
    m = trimesh.creation.cylinder(radius=r, height=h, sections=seksyen)
    m.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0]))
    v = np.asarray(m.vertices, dtype=np.float64) + np.array([x, y, z], dtype=np.float64)
    return v, np.asarray(m.faces, dtype=np.int64)


def bahagian(parts, v, f, warna):
    parts.append((np.asarray(v, dtype=np.float64),
                  np.asarray(f, dtype=np.int64),
                  tuple(int(c) for c in warna[:3])))


def gabung_kumpulan(parts):
    """Kumpul bahagian ikut warna -> {warna: (vertices, faces)} dengan offset betul."""
    kumpulan = {}
    for v, f, warna in parts:
        kumpulan.setdefault(warna, []).append((v, f))
    keluaran = {}
    for warna, senarai in kumpulan.items():
        semua_v, semua_f, ofset = [], [], 0
        for v, f in senarai:
            semua_v.append(v)
            semua_f.append(f + ofset)
            ofset += len(v)
        keluaran[warna] = (np.vstack(semua_v), np.vstack(semua_f))
    return keluaran


# ============================================================
# MODEL A - Bangunan konsep komersial/industri (mod meja)
# ============================================================
# Blok 2 tingkat: tapak 12m x 8m, tinggi keseluruhan ~8.2m
# Titik asal (0,0,0) = tengah tapak, aras tanah

WARNA_ALAS    = (196, 192, 184)
WARNA_DINDING = (232, 228, 220)
WARNA_ATAS    = (222, 217, 208)
WARNA_KACA    = (86, 120, 138)
WARNA_KACA2   = (74, 106, 124)
WARNA_PINTU   = (58, 72, 84)
WARNA_KANOPI  = (150, 141, 126)
WARNA_PARAPET = (206, 200, 190)
WARNA_EMAS    = (200, 169, 106)


def bina_bangunan():
    W, D = 12.0, 8.0
    H1, H2 = 4.2, 3.6
    p = []

    bahagian(p, *_kotak(W + 1.2, 0.20, D + 1.2, 0, 0.10, 0), WARNA_ALAS)

    bahagian(p, *_kotak(W, H1, D, 0, 0.20 + H1 / 2, 0), WARNA_DINDING)

    bahagian(p, *_kotak(W - 0.8, H2, D - 0.8, 0, 0.20 + H1 + H2 / 2, 0), WARNA_ATAS)

    for zz in (D / 2 + 0.01, -D / 2 - 0.01):
        bahagian(p, *_kotak(W - 2.6, 1.9, 0.06, 0, 0.20 + 1.9, zz), WARNA_KACA)
    for xx in (W / 2 + 0.01, -W / 2 - 0.01):
        bahagian(p, *_kotak(0.06, 1.9, D - 2.2, xx, 0.20 + 1.9, 0), WARNA_KACA)

    for zz in ((D - 0.8) / 2 + 0.01, -(D - 0.8) / 2 - 0.01):
        bahagian(p, *_kotak(W - 2.0, 1.6, 0.06, 0, 0.20 + H1 + 1.7, zz), WARNA_KACA2)

    bahagian(p, *_kotak(2.0, 2.6, 0.10, 0, 0.20 + 1.3, D / 2 + 0.02), WARNA_PINTU)
    bahagian(p, *_kotak(4.4, 0.16, 1.8, 0, 0.20 + 3.0, D / 2 + 0.85), WARNA_KANOPI)

    top = 0.20 + H1 + H2
    bahagian(p, *_kotak(W - 0.8, 0.45, 0.16, 0, top + 0.22, (D - 0.8) / 2), WARNA_PARAPET)
    bahagian(p, *_kotak(W - 0.8, 0.45, 0.16, 0, top + 0.22, -(D - 0.8) / 2), WARNA_PARAPET)
    bahagian(p, *_kotak(0.16, 0.45, D - 0.8, (W - 0.8) / 2, top + 0.22, 0), WARNA_PARAPET)
    bahagian(p, *_kotak(0.16, 0.45, D - 0.8, -(W - 0.8) / 2, top + 0.22, 0), WARNA_PARAPET)

    # jalur aksen emas Zentra — menonjol 0.12m supaya jelas kelihatan
    bahagian(p, *_kotak(W + 0.24, 0.30, D + 0.24, 0, 0.20 + H1, 0), WARNA_EMAS)

    return p


# ============================================================
# MODEL B - Sofa 3 tempat duduk
# ============================================================
# 2.10m (lebar) x 0.92m (dalam) x 0.80m (tinggi)

W_KAKI   = (168, 138, 88)
W_BAWAH  = (60, 64, 72)
W_BADAN  = (96, 104, 118)
W_KUSYEN = (108, 116, 132)
W_BANTAL = (100, 108, 124)
W_SISI   = (92, 100, 116)


def bina_sofa():
    W, D = 2.10, 0.92
    p = []

    # Kaki MESTI menonjol di bawah tapak (kelemahan asal: tapak duduk pada 0.06m,
    # kaki hanya 6cm kelihatan -> sofa nampak seperti blok di atas lantai).
    for sx in (-1, 1):
        for sz in (-1, 1):
            bahagian(p, *_silinder(0.040, 0.20,
                                   sx * (W / 2 - 0.11), 0.10, sz * (D / 2 - 0.11), 12), W_KAKI)

    bahagian(p, *_kotak(W, 0.16, D, 0, 0.28, 0), W_BAWAH)                   # tapak
    bahagian(p, *_kotak(W, 0.26, D - 0.06, 0, 0.49, 0), W_BADAN)            # badan

    cw = (W - 0.16) / 3
    for i in range(3):
        cx = -W / 2 + 0.08 + cw / 2 + i * cw
        bahagian(p, *_kotak(cw - 0.04, 0.18, D - 0.14, cx, 0.71, 0.02), W_KUSYEN)    # kusyen
        bahagian(p, *_kotak(cw - 0.04, 0.34, 0.20, cx, 0.78, -D / 2 + 0.14), W_BANTAL)  # bantal

    for sx in (-1, 1):                                                      # penyandar sisi
        bahagian(p, *_kotak(0.14, 0.34, D, sx * (W / 2 - 0.07), 0.70, 0), W_SISI)

    return p


# ============================================================
# Eksport GLB - satu primitif per bahan
# ============================================================

def eksport_glb(kumpulan, path: Path) -> dict:
    adegan = trimesh.Scene()
    for i, (warna, (v, f)) in enumerate(sorted(kumpulan.items(), key=lambda kv: -len(kv[1][1]))):
        m = trimesh.Trimesh(vertices=v, faces=f, process=False)
        m.visual = trimesh.visual.TextureVisuals(
            material=trimesh.visual.material.PBRMaterial(
                name=f"mat_{i}",
                baseColorFactor=[c / 255.0 for c in warna] + [1.0],
                metallicFactor=0.05,
                roughnessFactor=0.78,
                doubleSided=True,
            )
        )
        adegan.add_geometry(m, node_name=f"part_{i}", geom_name=f"part_{i}")
    glb = adegan.export(file_type="glb")
    path.write_bytes(glb)
    return {"fail": path.name, "bait": path.stat().st_size, "primitif": len(kumpulan)}


# ============================================================
# Eksport USDZ
# ============================================================

def _align_usdz(path: Path):
    """Tulis semula arkib USDZ supaya data setiap fail bermula pada gandaan 64 bait.
    USDZ ialah ZIP TANPA mampatan; iOS memerlukan penjajaran 64-bait."""
    src = path.read_bytes()
    entries, pos = [], 0
    while True:
        i = src.find(b"PK\x03\x04", pos)
        if i < 0:
            break
        hdr = src[i:i + 30]
        if len(hdr) < 30:
            break
        name_len = struct.unpack("<H", hdr[26:28])[0]
        extra_len = struct.unpack("<H", hdr[28:30])[0]
        csize = struct.unpack("<I", hdr[18:22])[0]
        name = src[i + 30:i + 30 + name_len]
        extra = src[i + 30 + name_len:i + 30 + name_len + extra_len]
        d0 = i + 30 + name_len + extra_len
        entries.append((name, extra, src[d0:d0 + csize]))
        pos = d0 + csize

    out, central = bytearray(), []
    for name, extra, data in entries:
        # Penjajaran 64-bait mesti pada DATA, bukan pada kepala tempatan.
        # Isi baki dengan medan 'extra' sifar (cara usdzip Apple).
        while len(out) % 64 != 0:
            out += b"\x00"
        offset = len(out)
        asas_data = offset + 30 + len(name) + len(extra)
        pad = (64 - (asas_data % 64)) % 64
        extra_pad = extra + (b"\x00" * pad)
        crc = zipfile.crc32(data) & 0xFFFFFFFF
        out += struct.pack("<IHHHHHIIIHH", 0x04034b50, 20, 0, 0, 0, 0, crc,
                           len(data), len(data), len(name), len(extra_pad))
        out += name + extra_pad + data
        assert len(out) - len(data) - offset - 30 - len(name) - len(extra_pad) == 0
        central.append((name, extra_pad, crc, len(data), offset))
    cd_start = len(out)
    cd = bytearray()
    for name, extra, crc, size, offset in central:
        cd += struct.pack("<IHHHHHHIIIHHHHHII", 0x02014b50, 20, 20, 0, 0, 0, 0, crc,
                          size, size, len(name), len(extra), 0, 0, 0, 0, offset)
        cd += name + extra
    out += cd
    out += struct.pack("<IHHHHIIH", 0x06054b50, 0, 0,
                       len(central), len(central), len(cd), cd_start, 0)
    path.write_bytes(bytes(out))


def eksport_usdz(kumpulan, nama, path: Path) -> dict:
    """Jana USDA dan pek sebagai USDZ (Y-up, 1 unit = 1 meter)."""
    from pxr import Usd, UsdGeom, UsdShade, Sdf, Gf, Vt

    _Y = getattr(UsdGeom.Tokens, "Y", None) or getattr(UsdGeom.Tokens, "y")
    _VERTEX = getattr(UsdGeom.Tokens, "vertex", None) or getattr(UsdGeom.Tokens, "Varying")

    stage = Usd.Stage.CreateInMemory()
    UsdGeom.SetStageUpAxis(stage, _Y)
    UsdGeom.SetStageMetersPerUnit(stage, 1.0)
    root = UsdGeom.Xform.Define(stage, "/Root")
    stage.SetDefaultPrim(root.GetPrim())

    bil = 0
    for i, (warna, (v, f)) in enumerate(sorted(kumpulan.items(), key=lambda kv: -len(kv[1][1]))):
        nama_p = f"{nama}_part{i}"
        m = UsdGeom.Mesh.Define(stage, f"/Root/{nama_p}")
        m.CreatePointsAttr(Vt.Vec3fArray([Gf.Vec3f(float(a), float(b), float(c))
                                          for a, b, c in v]))
        m.CreateFaceVertexCountsAttr(Vt.IntArray([3] * len(f)))
        m.CreateFaceVertexIndicesAttr(Vt.IntArray([int(x) for x in np.asarray(f).flatten()]))
        m.CreateSubdivisionSchemeAttr("none")
        t0, t1, t2 = v[f[:, 0]], v[f[:, 1]], v[f[:, 2]]
        fn = np.cross(t1 - t0, t2 - t0)
        ln = np.linalg.norm(fn, axis=1, keepdims=True)
        ln[ln == 0] = 1.0
        normals = np.repeat(fn / ln, 3, axis=0)
        m.CreateNormalsAttr(Vt.Vec3fArray([Gf.Vec3f(float(a), float(b), float(c))
                                           for a, b, c in normals]))
        m.SetNormalsInterpolation(_VERTEX)
        col = Gf.Vec3f(warna[0] / 255.0, warna[1] / 255.0, warna[2] / 255.0)
        UsdGeom.Gprim(m).CreateDisplayColorAttr(Vt.Vec3fArray([col]))
        mp = UsdShade.Material.Define(stage, f"/Root/M_{nama_p}")
        sh = UsdShade.Shader.Define(stage, f"/Root/M_{nama_p}/Surface")
        sh.CreateIdAttr("UsdPreviewSurface")
        sh.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set(col)
        sh.CreateInput("metallic", Sdf.ValueTypeNames.Float).Set(0.05)
        sh.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(0.78)
        mp.CreateSurfaceOutput().ConnectToSource(sh.ConnectableAPI(), "surface")
        UsdShade.MaterialBindingAPI.Apply(m.GetPrim()).Bind(mp)
        bil += 1

    usda = stage.GetRootLayer().ExportToString()
    tmp = path.with_suffix(".tmp.usdz")
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_STORED) as z:
        zi = zipfile.ZipInfo(f"{nama}.usda")
        zi.compress_type = zipfile.ZIP_STORED
        zi.date_time = (2026, 9, 28, 0, 0, 0)
        zi.external_attr = 0o644 << 16
        z.writestr(zi, usda.encode("utf-8"))
    _align_usdz(tmp)
    tmp.replace(path)
    return {"fail": path.name, "bait": path.stat().st_size, "bahagian": bil}


# ============================================================
# Semakan kendiri
# ============================================================

def rahsia_align(path: Path) -> bool:
    """Sahkan DATA setiap entri bermula pada gandaan 64 bait (keperluan USDZ)."""
    src = path.read_bytes()
    ok = True
    pos = 0
    while True:
        i = src.find(b"PK\x03\x04", pos)
        if i < 0:
            break
        hdr = src[i:i + 30]
        nl = struct.unpack("<H", hdr[26:28])[0]
        el = struct.unpack("<H", hdr[28:30])[0]
        d0 = i + 30 + nl + el
        if d0 % 64 != 0:
            ok = False
        pos = d0
    return ok


def main():
    hasil = {}
    for nama, fn in (("bangunan-konsep", bina_bangunan), ("sofa-3-seater", bina_sofa)):
        parts = fn()
        kumpulan = gabung_kumpulan(parts)
        semua_v = np.vstack([v for v, f in kumpulan.values()])
        lo, hi = semua_v.min(axis=0), semua_v.max(axis=0)
        glb = eksport_glb(kumpulan, OUT / f"{nama}.glb")
        usdz = eksport_usdz(kumpulan, nama.replace("-", "_"), OUT / f"{nama}.usdz")
        hasil[nama] = {
            "glb": glb,
            "usdz": usdz,
            "saiz_meter": [round(float(s), 3) for s in (hi - lo)],
            "y_min": round(float(lo[1]), 4),
            "tengah_xz": [round(float((lo[0] + hi[0]) / 2), 4),
                          round(float((lo[2] + hi[2]) / 2), 4)],
            "usdz_selaras_64": rahsia_align(OUT / f"{nama}.usdz"),
        }
    print(json.dumps(hasil, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
