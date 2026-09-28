#!/usr/bin/env python3
"""Jana kod QR Fasa 0 untuk halaman AR ZENTRA VR3D.

Kod QR mesti menunjuk ke URL HTTPS sebenar — kamera telefon memerlukan HTTPS.
Disemak dengan pembaca QR berprogram supaya tidak menghantar kod yang tidak boleh dibaca.
"""
import json
from pathlib import Path

# Laluan relatif kepada lokasi skrip -> boleh dijalankan dari mana-mana.
AKAR = Path(__file__).resolve().parent.parent

import qrcode
from qrcode.constants import ERROR_CORRECT_M
from PIL import Image, ImageDraw, ImageFont

PANGKAL = "https://vr3d.zentrapropertygroup.com"
AKAR = AKAR
KELUAR = AKAR / "site" / "assets" / "qr"
KELUAR.mkdir(parents=True, exist_ok=True)

NAVY, EMAS = (7, 21, 37), (200, 169, 106)


def jana(url: str, nama: str, kapsyen: str, saiz_kotak: int = 10) -> dict:
    q = qrcode.QRCode(version=None, error_correction=ERROR_CORRECT_M,
                      box_size=saiz_kotak, border=4)
    q.add_data(url)
    q.make(fit=True)
    im = q.make_image(fill_color="black", back_color="white").convert("RGB")

    # bingkai jenama: jalur navy + emas di bawah, kapsyen
    W, H = im.size
    jalur = 76
    kad = Image.new("RGB", (W, H + jalur), NAVY)
    kad.paste(im, (0, 0))
    d = ImageDraw.Draw(kad)
    d.rectangle([0, H, W, H + 4], fill=EMAS)
    try:
        f1 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
        f2 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 15)
    except Exception:
        f1 = f2 = ImageFont.load_default()
    d.text((14, H + 12), "ZENTRA VR3D · AR", font=f1, fill=EMAS)
    d.text((14, H + 40), kapsyen, font=f2, fill=(200, 210, 220))

    fp = KELUAR / f"{nama}.png"
    kad.save(fp, optimize=True)
    return {"nama": nama, "url": url, "fail": f"assets/qr/{nama}.png",
            "px": list(kad.size), "bait": fp.stat().st_size, "kapsyen": kapsyen}


def baca_balik(fp: Path) -> str:
    """Baca kod QR semula (dekod) — bukti ia benar-benar boleh diimbas."""
    try:
        from pyzbar.pyzbar import decode
        res = decode(Image.open(fp))
        return res[0].data.decode() if res else ""
    except Exception as e:
        return f"<dekod tiada: {e}>"


if __name__ == "__main__":
    senarai = [
        jana(f"{PANGKAL}/ar/", "ar-hab", "Hab AR — pilih model"),
        jana(f"{PANGKAL}/ar/viewer.html?m=bangunan-konsep", "ar-bangunan",
             "Bangunan Konsep — lihat dalam AR"),
        jana(f"{PANGKAL}/ar/viewer.html?m=sofa-3-seater", "ar-sofa",
             "Sofa 3 Tempat — lihat dalam AR"),
    ]
    for s in senarai:
        s["dekod"] = baca_balik(KELUAR / f"{s['nama']}.png")
    print(json.dumps(senarai, ensure_ascii=False, indent=2))
