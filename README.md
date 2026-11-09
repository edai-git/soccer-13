# SOCCER13 (`soccer13`) — PC → PS4 HEN Compatibility Port

<p align="center">
  <img src="assets/logo.png" alt="SOCCER 13 Logo" width="480"><br>
  <em>Clean-room Native Compatibility Port & Standalone Launcher untuk PlayStation 4 (PS4 HEN)</em>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/status-HEN--Tested--Playable-brightgreen" alt="Status">
  <img src="https://img.shields.io/badge/target-PS4_HEN-003791" alt="Target">
  <img src="https://img.shields.io/badge/build-Docker_Reproducible-2496ED" alt="Build">
  <img src="https://img.shields.io/badge/language-C%20%2F%20C%2B%2B-00599C" alt="Language">
  <img src="https://img.shields.io/badge/graphics-DXVK%20D3D9%20%E2%86%92%20RADV%201080p-orange" alt="Graphics">
</p>

<p align="center">
  <img src="assets/bg.jpg" alt="SOCCER 13 Background" width="720"><br>
  <em>Tampilan Visual Antarmuka SOCCER 13 di PS4</em>
</p>

**SOCCER13** (`soccer13`) adalah aplikasi homebrew dan port kompatibilitas untuk menjalankan salinan pribadi game sepak bola klasik tahun 2013 versi Windows PC secara langsung di **PlayStation 4 (PS4 HEN)** menggunakan pendekatan *compatibility layer* berbasis [`plastikman/orbis-win`](https://github.com/plastikman/orbis-win) dan mengadaptasi arsitektur dari [`7tg/futbol13`](https://github.com/7tg/futbol13).

> **Prinsip Utama:**  
> *"Do not rebuild the game. Run the original Windows game through a PS4-compatible runtime."*  
> Proyek **`soccer13`** tidak membuat ulang kode sumber, gameplay, maupun menyertakan aset berhak cipta. Seluruh binary dan aset game milik pengguna dijalankan di atas runtime kompatibilitas PS4 dengan **Direct Autoboot Launcher** atau antarmuka **Native PS4 Homebrew Launcher (`SOCCER13`)**.

---

## Daftar Isi

1. [Gambaran Umum & Mode Operasi](#1-gambaran-umum--mode-operasi)
2. [Arsitektur Teknis](#2-arsitektur-teknis)
3. [Fitur Utama](#3-fitur-utama)
4. [Struktur Proyek](#4-struktur-proyek)
5. [Sistem Build (Docker)](#5-sistem-build-docker)
6. [Instalasi & Penggunaan pada PS4](#6-instalasi--penggunaan-pada-ps4)
7. [Panduan Patching & Modding](#7-panduan-patching--modding)
8. [Pemetaan Kontroler (DualShock 4)](#8-pemetaan-kontroler-dualshock-4)
9. [Status Pengembangan (Roadmap)](#9-status-pengembangan-roadmap)
10. [Strategi Pengujian & Catatan Hardware](#10-strategi-pengujian--catatan-hardware)
11. [Batasan Ruang Lingkup & Legalitas](#11-batasan-ruang-lingkup--legalitas)
12. [Referensi](#12-referensi)

---

## 1. Gambaran Umum & Mode Operasi

Project **SOCCER13** mendukung 2 metode instalasi dan peluncuran:

### Mode 1: Standalone All-In-One PKG (`SOCCER13-FULL-PS4.pkg`) *(Disarankan)*
* Seluruh runtime `orbis-win`, Wine prefix, DXVK, konfigurasi `settings.dat`, stub *Direct Autoboot*, dan aset game (~5.5 GB) terkemas ke dalam **satu file installer `.pkg` mandiri (~6.06 GB)** dengan tipe `pkg_ps4_app`.
* **Pengalaman Pemain:** Pengguna cukup menginstal 1 file PKG lewat *GoldHEN Package Installer*. Saat game dibuka, game langsung melakukan *direct autoboot* ke gameplay (Preset High 1080p 60 FPS) tanpa perlu setup manual, tanpa Wine desktop, dan tanpa koneksi FTP/USB.

### Mode 2: Modular Baseline PKG (`SOCCER13-PS4.pkg`) + External Loading
* Hanya runtime dan launcher native yang dikemas ke dalam PKG kecil (~500 MB).
* File instalasi game PC disalin oleh pengguna ke konsol melalui USB atau FTP ke direktori `/data/prospero-win/prefixes/soccer13/drive_c/Games/SOCCER13/`. Cocok untuk pengujian cepat atau debugging.

---

## 2. Arsitektur Teknis

```text
             WINDOWS PC GAME
                    |
              SOCCER13 PC
                    |
       +------------+------------+
       |                         |
       v                         v
   Game EXE                    img/
  (PE32 Binary)             Game Assets
       |                         |
       +------------+------------+
                    |
                    v
              WINE RUNTIME
                    |
       +------------+------------+
       |            |            |
       v            v            v
   Win32 API    DirectX 9     XInput
       |            |            |
       v            v            v
   Wine DLLs      DXVK       Input Mapping
       |            |            |
       +------------+------------+
                    |
                    v
           ORBIS-WIN PLATFORM
                    |
       +------------+------------+
       |            |            |
       v            v            v
    Orbis OS     Mesa/RADV    PS4 Native
                  Backend       Input
       |            |            |
       +------------+------------+
                    |
                    v
               PS4 HEN
                    |
                    v
            SOCCER13 GAMEPLAY (1080p High)
```

### Komponen Utama

| Komponen | Peran & Tanggung Jawab |
|---|---|
| **`orbis-win` Runtime** | Fondasi kompatibilitas Windows pada Orbis OS: integrasi Wine, manajemen memori, eksekusi CPU, audio runtime, dan jembatan ke sistem native PS4. |
| **Wine (Native WoW64)** | Menjalankan executable Windows PE32, menyediakan Win32 API, Windows registry, virtualisasi filesystem, XInput/DirectInput, dan DirectSound/XAudio. |
| **DXVK (v2.6.2)** | Menerjemahkan panggilan grafis Direct3D 9 menjadi Vulkan (shader translation, manajemen tekstur, render state, dan sinkronisasi frame). |
| **Mesa / RADV** | Backend driver grafis Vulkan untuk arsitektur GPU AMD GCN pada PS4, menangani alokasi memori GPU, command submission, dan display presentation. |
| **Direct Autoboot Stub (`handoff_stub.c`)** | Launcher binary berbobot ringan (~34 KB) dengan layout *no-RELRO* murni yang langsung memprovisi prefix, menginisialisasi `settings.dat`, dan meluncurkan game tanpa perantara menu manual. |
| **Native Launcher UI (`app/launcher/`)** | Aplikasi antarmuka native PS4 dengan Model 1 Graphical Preset Selector (`High`, `Balance`, `Medium`, `Low`) berbasis kontroler DualShock 4. |

---

## 3. Fitur Utama

- **Direct Autoboot Seamless:** Menghilangkan keharusan membuka Wine desktop / menekan X pada home screen; game langsung masuk ke intro, menu, dan pertandingan.
- **Preset Grafis High 1080p Terintegrasi:** Menghasilkan file biner `settings.dat` (852-byte, checksum CRC-16/XMODEM) secara dinamis dengan resolusi 1920×1080, Fullscreen, Kualitas High, dan VSync aktif.
- **Model 1 Graphical Preset Selector:** Opsi antarmuka vertikal berbasis D-Pad dengan urutan prioritas performa `[High (rata-kanan)]` $\rightarrow$ `[Balance]` $\rightarrow$ `[Medium]` $\rightarrow$ `[Low]`.
- **Solusi Tuntas Instalasi PKG (Error 2157510736 / 0x80990050):** Menggunakan format `pkg_ps4_app` (`ContentType.GD`) murni berkat patch otomatis pada `PkgTool.Core` yang menyelesaikan bug buffer PlayGo ChunkSha pada paket besar (>2.2 GB).
- **Proteksi Save Data Non-Destruktif:** Struktur direktori save (`Documents/KONAMI/.../save/`) yang berisi `EDIT.bin`, Option File, dan Master League diisolasi sehingga tidak terhapus saat pembaruan prefix.
- **Pipeline Dump Otomatis (`scripts/dump-from-ps4.py`):** Script penarik aset game dan Wine registry seed tervalidasi langsung dari PS4 via FTP ke workspace lokal PC.
- **100% Dockerized Build:** Seluruh kompilasi C/C++, pembuatan stub, patching tool, dan pengemasan PKG berjalan di container Docker yang terisolasi dan *reproducible*.

---

## 4. Struktur Proyek

```text
soccer13/
├── docker/
│   ├── Dockerfile              # Container build dengan dependency yang dipin (@sha256)
│   ├── docker-compose.yml      # Konfigurasi service builder & volume cache
│   ├── build-env.sh            # Inisialisasi environment & verifikasi checksum
│   └── dependencies.lock       # Lockfile versi SDK, commit submodule, & SHA-256
├── runtime/
│   └── orbis-win/              # Submodule upstream plastikman/orbis-win
├── app/
│   ├── assets/                 # icon0.png, pic0.png, pic1.png, bg.raw
│   ├── launcher/               # Source code Launcher C/C++
│   │   ├── src/
│   │   │   ├── handoff_stub.c  # Direct Autoboot Stub (no-RELRO)
│   │   │   ├── launcher_ui.c   # Model 1 Preset Selector
│   │   │   ├── launcher_video.c# Direct VideoOut PS4
│   │   │   └── main.c          # Launcher entrypoint
│   │   └── include/
│   ├── profiles/
│   │   └── soccer13.profile    # Runtime & Wine environment profile untuk SOCCER13
│   └── config/
│       ├── dxvk.conf           # Konfigurasi DXVK D3D9 untuk RADV PS4
│       └── settings-template/  # Template settings.dat & registry Windows
├── scripts/
│   ├── build.sh                # Kompilasi seluruh komponen
│   ├── test.sh                 # Eksekusi unit test & validasi
│   ├── release.sh              # Pembuatan paket rilis baseline
│   ├── package.sh              # Pembuatan Standalone PKG (SOCCER13-FULL-PS4.pkg)
│   ├── dump-from-ps4.py        # Penarik dump game & registry dari PS4 via FTP
│   └── validate.sh             # Validasi artefak, lisensi, & clean-room
├── tests/
│   ├── launcher/               # Unit test logika launcher & state machine
│   ├── config/                 # Test generator/parser settings.dat & profile
│   ├── package/                # Validasi struktur PKG & kebersihan clean-room
│   └── integration/            # Test integrasi staging pipeline
├── docs/                       # Dokumentasi teknis, audit Phase 0, & panduan
├── artifacts/                  # Direktori output hasil build (.pkg, log, checksum)
├── prd.md                      # Product Requirements Document
├── dump.md                     # Spesifikasi teknis dump & standalone packaging
├── AGENTS.md                   # Instruksi operasional AI Coding Agent
└── README.md                   # Dokumentasi utama proyek
```

---

## 5. Sistem Build (Docker)

Semua proses build dijalankan di dalam Docker container tanpa bergantung pada toolchain compiler di mesin host.

### Perintah Build Standar

```bash
# 1. Build Docker image
docker compose build

# 2. Jalankan host tests (unit test, config check, clean-room hygiene)
docker compose run --rm builder test

# 3. Buat Standalone All-in-One PKG (6.1 GB)
docker compose run --rm builder ./scripts/package.sh

# 4. Bersihkan workspace build
docker compose run --rm builder clean
```

---

## 6. Instalasi & Penggunaan pada PS4

### Langkah Instalasi Standalone PKG (`SOCCER13-FULL-PS4.pkg`)

1. **Salin ke USB Drive:**
   * Siapkan flashdisk atau harddisk eksternal dengan format **exFAT**.
   * Salin file `artifacts/SOCCER13-FULL-PS4.pkg` ke root drive USB.
2. **Instal melalui GoldHEN:**
   * Tancapkan USB ke konsol PS4 yang sudah mengaktifkan HEN / GoldHEN.
   * Masuk ke **Settings → GoldHEN → Package Installer**.
   * Pilih **`SOCCER13-FULL-PS4.pkg`** dan tekan **X** untuk menginstal.
3. **Mulai Bermain:**
   * Buka **SOCCER 13** dari Home Screen PS4.
   * Game akan langsung melakukan boot ke PES 2013 dengan pengaturan grafis High 1080p.

---

## 7. Panduan Patching & Modding

Jika Anda ingin memasang patch (seperti update pemain, transfer, Option File, atau kitserver), **Anda TIDAK PERLU melakukan dump ulang dari PS4** karena aset dasar 5.5 GB sudah tersimpan di PC Anda.

| Jenis Patch | Kebutuhan Repack PKG? | Cara Pemasangan |
|---|---|---|
| **Option File / Transfer (`EDIT.bin`)** | **Tidak Perlu** | Cukup kirim file `EDIT.bin` via FTP ke PS4:<br>`/data/prospero-win/prefixes/soccer13/drive_c/users/prospero/Documents/KONAMI/Pro Evolution Soccer 2013/save/EDIT.bin` |
| **Testing Patch Cepat di PS4** | **Tidak Perlu** | Kirim file patch/mod langsung via FTP ke folder game internal di PS4:<br>`/data/prospero-win/prefixes/soccer13/drive_c/Games/SOCCER13/` |
| **Kemas Menjadi File PKG Baru** | **Ya** (Cukup di PC) | 1. Letakkan file patch baru ke `build/ps4-dump/game/SOCCER13/` di PC.<br>2. Jalankan `docker compose run --rm builder ./scripts/package.sh`.<br>3. Install file `.pkg` baru yang dihasilkan. |

---

## 8. Pemetaan Kontroler (DualShock 4)

Navigasi menu dan gameplay didukung penuh melalui kontroler **DualShock 4** via emulasi XInput:

| Tombol DualShock 4 | Fungsi di SOCCER13 |
|---|---|
| **Left Stick / D-Pad** | Pergerakan Pemain & Navigasi Menu |
| **Cross (✕)** | Umpan Pendek (*Pass*) / Konfirmasi |
| **Circle (○)** | Umpan Lambung (*Cross*) / *Sliding Tackle* |
| **Square (□)** | Tembakan (*Shoot*) / *Teammate Pressure* |
| **Triangle (△)** | Umpan Terobosan (*Through Pass*) / Kiper Maju |
| **L1** | Ganti Pemain (*Player Switch*) |
| **L2** | Kontrol Manual / Strategi |
| **R1** | Lari Cepat (*Sprint*) |
| **R2** | Kontrol Rapat (*Special Control / Modifier*) |
| **Options** | Jeda Pertandingan (*Pause*) / Menu Utama |

---

## 9. Status Pengembangan (Roadmap)

- [x] **Phase 0 — Repository Audit:** Pemetaan dependency, analisis `orbis-win` vs `futbol13`, dan penyusunan 5 dokumen teknis.
- [x] **Phase 1 — Docker Build Infrastructure:** Pipeline Docker multi-stage yang reproducible, verifikasi SHA-256, dan pinning dependency.
- [x] **Phase 2 — Baseline Runtime:** Kompilasi baseline `orbis-win` ke format PS4 PKG dan validasi eksekusi kernel/Wine.
- [x] **Phase 3 — SOCCER13 Integration:** Pembuatan `soccer13.profile`, DXVK 2.6.2, generator biner `settings.dat`, dan Wine registry seed.
- [x] **Phase 4 — Game Compatibility:** Validasi 12 tahap eksekusi di hardware PS4 target (mencapai gameplay stabil di 1080p High).
- [x] **Phase 5 — Launcher Integration:** Pengembangan Native Launcher UI (Model 1 Preset Selector) dan Direct Autoboot Stub (no-RELRO).
- [x] **Phase 6 — Standalone Release:** Script dump FTP (`scripts/dump-from-ps4.py`), perbaikan root cause error instalasi `2157510736` (`pkg_ps4_app`), patch PlayGo ChunkSha `PkgTool.Core`, dan produksi `SOCCER13-FULL-PS4.pkg` (6.1 GB).

---

## 10. Strategi Pengujian & Catatan Hardware

Setiap build diverifikasi dengan pengujian berlapis:
1. **Host Tests (Docker):** 26 unit & integration tests (`python -m unittest discover -s tests`) yang memvalidasi CRC `settings.dat`, skema profile, struktur staging, ketiadaan IP hardcoded, serta kebersihan file proprietary dalam git.
2. **Hardware Target (PS4 HEN):**
   * **Model:** PS4 Fat / Slim / Pro
   * **Firmware Target:** 9.00 / 11.00 (GoldHEN)
   * **Resolusi & Refresh Rate:** 1920×1080 @ 60 Hz via DXVK D3D9
   * **Status Log:** `/data/prospero-win/logs/` (mencatat sesi Wine & runtime Orbis)

---

## 11. Batasan Ruang Lingkup & Legalitas

### Kebijakan Clean-Room
Proyek ini mematuhi standar *clean-room reverse-engineering* secara ketat:
* **Tidak ada binary game, `.exe`, `.dll`, file `.img`, maupun firmware konsol yang di-commit ke dalam repositori Git.**
* File dump game milik pengguna disimpan secara lokal di folder `build/` yang di-ignore oleh Git (`.gitignore`).
* Semua nama, teks antarmuka, dan karya seni yang disertakan dalam repositori menggunakan identitas netral **`SOCCER13`**.

### Disclaimer Legal
**SOCCER13** (`soccer13`) adalah proyek kompatibilitas dan launcher sumber terbuka independen yang **tidak berafiliasi dengan Konami Digital Entertainment maupun Sony Interactive Entertainment**. Seluruh merek dagang dan hak cipta game adalah milik pemiliknya masing-masing. Pengguna wajib memiliki salinan resmi game PC asli untuk menggunakan proyek ini.

---

## 12. Referensi

- **orbis-win (Base PS4 Runtime):** [https://github.com/plastikman/orbis-win](https://github.com/plastikman/orbis-win)
- **FUTBOL13 (PS5 Reference Implementation):** [https://github.com/7tg/futbol13](https://github.com/7tg/futbol13)
- **OpenOrbis PS4 Toolchain:** [https://github.com/OpenOrbis/OpenOrbis-PS4-Toolchain](https://github.com/OpenOrbis/OpenOrbis-PS4-Toolchain)
- **Dokumen Perencanaan Dump & Standalone PKG:** [dump.md](./dump.md)
- **Instruksi AI Coding Agent:** [AGENTS.md](./AGENTS.md)
