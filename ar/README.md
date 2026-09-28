# ZENTRA VR3D — Modul Augmented Reality (AR)

Modul AR untuk [vr3d.zentrapropertygroup.com](https://vr3d.zentrapropertygroup.com).
Ia **sambungan** kepada sistem tur panorama sedia ada — bukan sistem berasingan. Ia berkongsi
repositori aset, pengedaran kod QR, dan penjejak analitik.

> **Fasa 0 — bukti konsep.** Satu model projek dan satu item perabot, butang AR berfungsi di
> kedua-dua platform. Fasa 1 (katalog perabot + peletakan) belum bermula.

## Halaman

| Fail | Tujuan |
|---|---|
| `ar/index.html` | Hab AR — memuat katalog dari manifest, memapar keupayaan peranti |
| `ar/viewer.html` | Pelayar AR universal — `?m=<kunci>` memilih model |
| `ar/qr.html` | Kod QR untuk cetakan (papan tanda tapak, risalah) |
| `ar/ar.css` | Gaya kongsi kedua-dua halaman (navy `#071525` + emas `#C8A96A`) |
| `ar/ar-detect.js` | Pengesanan ciri + penghalaan peranti |

## Penghalaan Peranti

Penghalaan menggunakan **pengesanan ciri sahaja** — bukan `navigator.platform`. UA mudah
dipalsukan dan mudah basi.

| Peranti | Ciri dikesan | Laluan |
|---|---|---|
| iPhone / iPad (Safari) | `rel="ar"` (Quick Look) | `ios-src` USDZ → AR asli iOS |
| Android (Chrome) | `navigator.xr.isSessionSupported('immersive-ar')` | WebXR / Scene Viewer |
| Desktop | tiada | Pratonton 3D sahaja (butang AR disembunyikan) |

**iPhone TIDAK menyokong WebXR `immersive-ar`.** Artikel dalam talian yang mendakwa Safari 18
menyokongnya adalah **salah**. Setiap model mesti ada dua format: `.glb` (Android) dan `.usdz` (iOS).

## Peraturan Model

1. **1 unit = 1 meter** dalam kedua-dua glTF dan USD.
2. **Titik asal di tengah pangkal** — x=0, z=0 di tengah tapak; y=0 pada aras tanah.
3. **Y-up** untuk kedua-dua format.
4. Nama fail: huruf kecil, tanda sempang (`bangunan-konsep.glb`). Fail di dalam USDZ menggunakan
   garis bawah (`bangunan_konsep.usda`) — itu normal.
5. Saiz sasaran: perabot < 5 MB, bangunan < 25 MB.

## Membina Semula

```bash
python3 -m venv ~/.venvs/ar
~/.venvs/ar/bin/pip install trimesh numpy pillow usd-core "qrcode[pil]" pyzbar

cd <akar-projek>
~/.venvs/ar/bin/python scripts/bina_model.py     # GLB + USDZ  -> models/
~/.venvs/ar/bin/python scripts/sah_model.py      # sahkan skala, titik asal, padanan GLB/USDZ
~/.venvs/ar/bin/python scripts/jana_qr.py        # kod QR      -> site/assets/qr/
python3 scripts/susun_tapak.py                   # susun tapak + semak rujukan
```

Skrip menggunakan laluan relatif kepada lokasi skrip, jadi ia boleh dijalankan dari mana-mana.
Struktur yang dijangka: `<akar>/scripts/` + `<akar>/models/` + `<akar>/site/`.

## Perangkap Yang Sudah Diketahui

Setiap satu ini menyebabkan kegagalan sebenar semasa Fasa 0.

1. **`zipfile` mesti zip TANPA mampatan untuk USDZ**, dan **DATA** setiap entri mesti bermula pada
   gandaan 64 bait — bukan kepala tempatan. Isi baki dengan medan `extra` sifar (cara `usdzip` Apple).
   Jika tidak, AR Quick Look menolak fail tanpa mesej yang jelas.
2. **`trimesh.util.concatenate` membuang warna setiap bahagian.** Ia mengekalkan visual mesh pertama
   sahaja, jadi model berbilang warna menjadi satu warna. Gabung manual dengan menjejak warna
   setiap muka.
3. **`trimesh.creation.cylinder` mencipta silinder pada paksi Z**, bukan Y. Putar π/2 pada paksi X
   untuk silinder menegak (kaki perabot).
4. **`rel="ar"` memerlukan `<img>` sebagai anak tunggal terus** bagi anchor. `model-viewer` menjana
   ini sendiri dalam mod `quick-look`.
5. **Sediakan USDZ terlebih dahulu** — jangan tukar format pada masa ketukan. Penukaran mengambil
   beberapa saat dan AR Quick Look akan tamat masa.
6. `UsdGeom.Tokens.Y` tidak wujud dalam USD 26.8 — gunakan `UsdGeom.Tokens.y`.
7. **model-viewer dihos sendiri** (`assets/vendor/`) untuk membuang kebergantungan CDN pihak ketiga
   pada tapak produksi.

## MIME Jenis `.usdz`

AR Quick Look memerlukan `.usdz` dihidangkan sebagai `model/vnd.usdz+zip`.
**GitHub Pages tidak membenarkan penyesuaian `Content-Type`.** Semak status sebenar dengan:

```bash
curl -sI https://vr3d.zentrapropertygroup.com/models/projects/bangunan-konsep.usdz \
  | grep -i content-type
```

Jika ia bukan `model/vnd.usdz+zip`, iOS mungkin masih berfungsi (Safari melakukan sniff) tetapi
ini mesti disahkan pada peranti sebenar. Jika ia gagal, tapak perlu dihidangkan melalui hos yang
membenarkan penyesuaian kepala (contohnya pelayan Caddy Zentra), bukan GitHub Pages.

## Analitik

`assets/zvr3d-tracker.js` (dikongsi dengan modul tur) menyimpan acara dalam `localStorage`.
Acara AR yang dipancarkan:

`ar_hab_visit` · `ar_hab_katalog_ok` · `ar_keupayaan` · `ar_model_dipilih` ·
`ar_model_dimuat` · `ar_model_gagal` · `ar_dilancarkan` · `ar_objek_diletakkan` ·
`ar_gagal` · `ar_keluar` · `ar_pandangan_set_semula`

Baca melalui konsol pelayar: `ZVR3D_TRACKER.getData()`.

## Penafian

Visualisasi AR ialah **ilustrasi**, bukan tinjauan, ukuran tepat, atau reka bentuk yang diluluskan.
Jangan gunakan untuk mengesahkan sempadan, set back, atau dimensi.
