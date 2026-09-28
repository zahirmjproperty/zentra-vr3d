#!/usr/bin/env python3
"""Pemapar z-buffer sebenar (numpy) untuk semakan visual model Fasa 0.
Menggantikan pemapar 'painter's algorithm' yang tidak boleh dipercayai:
setiap piksel diuji kedalaman sebenar, normal diinterpolasi, tiada garis tepi palsu."""
import numpy as np
import trimesh
from pathlib import Path

# Laluan relatif kepada lokasi skrip -> boleh dijalankan dari mana-mana.
AKAR = Path(__file__).resolve().parent.parent
from PIL import Image

M = AKAR / "models"
OUT = AKAR / "preview"
OUT.mkdir(parents=True, exist_ok=True)

W, H = 1000, 720
BG = np.array([11, 21, 36], dtype=np.float64)


def kamera(az_deg, el_deg, jarak_faktor=2.35):
    az, el = np.radians(az_deg), np.radians(el_deg)
    pos = np.array([np.cos(el) * np.sin(az), np.sin(el), np.cos(el) * np.cos(az)])
    pos = pos / np.linalg.norm(pos)
    depan = -pos
    atas_dunia = np.array([0.0, 1.0, 0.0])
    kanan = np.cross(atas_dunia, depan)
    if np.linalg.norm(kanan) < 1e-9:
        kanan = np.array([1.0, 0.0, 0.0])
    kanan = kanan / np.linalg.norm(kanan)
    atas = np.cross(depan, kanan)
    return pos, kanan, atas, depan


def papar(mesh, az=-38, el=20, fov=34.0, langit=(0.42, 0.52, 0.62), tanah=(0.16, 0.19, 0.23),
          latar_pepejal=None):
    V = np.asarray(mesh.vertices, dtype=np.float64)
    F = np.asarray(mesh.faces, dtype=np.int64)
    try:
        fc = np.asarray(mesh.visual.face_colors, dtype=np.float64)[:, :3] / 255.0
        if fc.ndim == 1:
            fc = np.tile(fc, (len(F), 1))
    except Exception:
        fc = np.tile([0.78, 0.78, 0.78], (len(F), 1))

    pusat = (V.max(axis=0) + V.min(axis=0)) / 2
    jejari = float(np.linalg.norm(V.max(axis=0) - V.min(axis=0))) / 2

    pos, kanan, atas, depan = kamera(az, el)
    jarak = jejari / np.tan(np.radians(fov / 2)) * jarak_sebab()
    pos = pusat + pos * jarak

    # normal muka
    t0, t1, t2 = V[F[:, 0]], V[F[:, 1]], V[F[:, 2]]
    n = np.cross(t1 - t0, t2 - t0)
    ln = np.linalg.norm(n, axis=1, keepdims=True)
    ln[ln == 0] = 1
    n = n / ln
    # pastikan normal menghadap kamera
    pusat_muka = (t0 + t1 + t2) / 3
    arah = pos - pusat_muka
    tanda = np.sign(np.einsum("ij,ij->i", n, arah))
    tanda[tanda == 0] = 1
    n = n * tanda[:, None]

    # asas kamera
    rel = V - pos
    xc = rel @ kanan
    yc = rel @ atas
    zc = rel @ depan              # positif = di hadapan kamera

    f = (H / 2) / np.tan(np.radians(fov / 2))
    sx = W / 2 + (xc / zc) * f
    sy = H / 2 - (yc / zc) * f

    zbuf = np.full((H, W), 1e9)
    rbuf = np.tile(BG, (H, W, 1))

    # langit-gradien latar
    if latar_pepejal is not None:
        rbuf[:, :] = np.array(latar_pepejal, dtype=np.float64)
    else:
        for y in range(H):
            t = y / H
            rbuf[y, :] = np.array(langit) * (1 - t) + np.array(tanah) * t

    # rasterisasi
    for fi in range(len(F)):
        idx = F[fi]
        if np.any(zc[idx] <= 0.01):
            continue
        px = sx[idx]
        py = sy[idx]
        pz = zc[idx]

        x0, x1 = int(np.floor(px.min())), int(np.ceil(px.max()))
        y0, y1 = int(np.floor(py.min())), int(np.ceil(py.max()))
        x0, x1 = max(x0, 0), min(x1, W - 1)
        y0, y1 = max(y0, 0), min(y1, H - 1)
        if x0 > x1 or y0 > y1:
            continue

        xs = np.arange(x0, x1 + 1) + 0.5
        ys = np.arange(y0, y1 + 1) + 0.5
        gx, gy = np.meshgrid(xs, ys)

        d = (px[1] - px[0]) * (py[2] - py[0]) - (px[2] - px[0]) * (py[1] - py[0])
        if abs(d) < 1e-12:
            continue
        w0 = ((px[1] - gx) * (py[2] - gy) - (px[2] - gx) * (py[1] - gy)) / d
        w1 = ((px[2] - gx) * (py[0] - gy) - (px[0] - gx) * (py[2] - gy)) / d
        w2 = 1.0 - w0 - w1
        dalam = (w0 >= -1e-9) & (w1 >= -1e-9) & (w2 >= -1e-9)
        if not dalam.any():
            continue
        zz = w0 * pz[0] + w1 * pz[1] + w2 * pz[2]
        sub = zbuf[y0:y1 + 1, x0:x1 + 1]
        menang = dalam & (zz < sub)
        if not menang.any():
            continue
        sub[menang] = zz[menang]

        # pencahayaan Lambert dua arah + ambien hemisfera
        nn = n[fi]
        kunci = np.array([0.42, 0.80, 0.44]); kunci /= np.linalg.norm(kunci)
        isi = np.array([-0.55, 0.25, -0.6]); isi /= np.linalg.norm(isi)
        lam = max(float(nn @ kunci), 0.0)
        lam2 = max(float(nn @ isi), 0.0)
        c = fc[fi]
        terang = c * (0.30 + 0.70 * lam + 0.22 * lam2)
        # sedikit pemantul langit pada permukaan menghadap atas
        terang = terang + 0.055 * max(float(nn[1]), 0.0)
        terang = np.clip(terang, 0, 1)
        blok = rbuf[y0:y1 + 1, x0:x1 + 1]
        blok[menang] = terang

    return Image.fromarray((np.clip(rbuf, 0, 1) * 255).astype(np.uint8))


def jarak_sebab():
    return 1.0


def gabung_berwarna(adegan: trimesh.Scene) -> trimesh.Trimesh:
    """Gabung semua geometri scene KE DALAM satu mesh sambil MENGEKALKAN warna
    setiap bahagian. trimesh.util.concatenate membuang warna bahagian kedua dan
    seterusnya (ia mengekalkan visual mesh pertama sahaja) — jangan gunakannya."""
    V, F, C, ofset = [], [], [], 0
    for gname, g in adegan.geometry.items():
        try:
            faktor = g.visual.material.baseColorFactor
            c = tuple(float(x) for x in faktor[:3])
            # trimesh memulangkan baseColorFactor dalam skala 0-255
            if max(c) <= 1.001:
                c = tuple(x * 255 for x in c)
        except Exception:
            c = (200.0, 200.0, 200.0)
        v = np.asarray(g.vertices, dtype=np.float64)
        f = np.asarray(g.faces, dtype=np.int64) + ofset
        V.append(v); F.append(f)
        C.append(np.tile(np.array(c + (255.0,)), (len(f), 1)))
        ofset += len(v)
    m = trimesh.Trimesh(vertices=np.vstack(V), faces=np.vstack(F), process=False)
    m.visual = trimesh.visual.ColorVisuals(mesh=m, face_colors=np.vstack(C).astype(np.uint8))
    return m


hasil = []
for nama in ("bangunan-konsep", "sofa-3-seater"):
    adegan = trimesh.load(str(M / f"{nama}.glb"), force="scene")
    gab = gabung_berwarna(adegan)
    keping = []
    for az, el in ((-38, 20), (52, 16), (0, 4)):
        im = papar(gab, az=az, el=el, latar_pepejal=(0.90, 0.90, 0.92))
        keping.append(im)
    im = Image.new("RGB", (W, sum(k.height for k in keping)))
    y = 0
    for k in keping:
        im.paste(k, (0, y)); y += k.height
    fp = OUT / f"{nama}-zbuffer.png"
    im.save(fp)
    hasil.append((nama, fp.stat().st_size, im.size))

print("OK", hasil)
