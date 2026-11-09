# AGENTS.md — AI Coding Agent Instructions & Operational Guide

**Project:** `soccer13` (SOCCER13 PC → PS4 HEN)  
**Type:** Windows PC Game Compatibility Port  
**Target Platform:** PlayStation 4 (PS4 HEN)  
**Base Runtime:** [`plastikman/orbis-win`](https://github.com/plastikman/orbis-win)  
**Reference Implementation:** [`7tg/futbol13`](https://github.com/7tg/futbol13)  
**Primary Specification:** [prd.md](./prd.md)  
**Packaging Specification:** [dump.md](./dump.md)

---

## 1. Core Mandate, Naming & Philosophy

> **"Do not rebuild the game. Run the original Windows game through a PS4-compatible runtime (`soccer13`)."**

1. **Penamaan Netral (`soccer13` / `SOCCER13`):**  
   Seluruh identitas project, nama paket (`.pkg`), tampilan UI launcher, profil (`soccer13.profile`), Wine prefix (`prefixes/soccer13`), dan dokumentasi **wajib menggunakan nama `soccer13` / `SOCCER13`** (sebagaimana referensi PS5 menggunakan nama `futbol13` / `FUTBOL13`) guna menghindari pelanggaran hak cipta atau merek dagang pihak ketiga.
2. **Pendekatan Compatibility Layer:**  
   Project ini **bukan** dekompilasi, source port ulang, ataupun pembuatan ulang game engine. Tujuan project ini adalah menjalankan executable Windows 32-bit asli beserta aset `img/` milik pengguna di atas **PlayStation 4 (PS4 HEN)** menggunakan:
   - **`orbis-win`** sebagai fondasi runtime & integrasi Orbis OS
   - **Wine** untuk eksekusi PE32 & translasi Win32 API / XInput / DirectSound
   - **DXVK** untuk translasi Direct3D 9 ke Vulkan
   - **Mesa / RADV** sebagai backend grafis AMD GPU pada PS4
   - **Direct Autoboot Stub (`handoff_stub.c`) & Native PS4 Launcher (`SOCCER13`)** untuk manajemen instalasi, Wine prefix, konfigurasi `settings.dat`, input DualShock 4, dan logging

Setiap AI Coding Agent yang bekerja di repositori ini **wajib** mematuhi seluruh aturan, batasan arsitektur, dan tahapan kerja di dokumen ini sebelum menulis atau memodifikasi kode.

---

## 2. Mandatory Rules (Golden Rules)

AI Coding Agent **harus** mematuhi 18 aturan utama berikut tanpa pengecualian:

1. **Audit First:** Selesaikan audit arsitektur sebelum membuat perubahan radikal.
2. **Deep-Dive `orbis-win`:** Pelajari struktur, cara kerja, dan batasan [`plastikman/orbis-win`](https://github.com/plastikman/orbis-win) secara menyeluruh.
3. **Read Upstream Docs First:** Baca `AGENTS.md`, `docs/BUILDING.md`, `HARDWARE-STATUS.md`, dan seluruh dokumentasi build di upstream `orbis-win` sebelum menyentuh kode.
4. **Respect Upstream Foundation:** Gunakan `orbis-win` sebagai fondasi utama. Pisahkan dengan tegas antara kode upstream (`runtime/orbis-win/`), patch spesifik PS4, dan kode/konfigurasi khusus `soccer13` (`app/`).
5. **No Unjustified Component Swaps:** Jangan mengganti versi atau implementasi Wine, Mesa, RADV, atau DXVK tanpa alasan teknis yang terukur dan tervalidasi.
6. **PS4 ≠ PS5:** Jangan mengasumsikan fitur, kapasitas memori, path (`/data/prospero-win/` vs path Orbis), atau ekstensi Vulkan pada PS5 (`prospero-win` / `futbol13`) otomatis tersedia di PS4 (`orbis-win`). Selalu verifikasi kapabilitas RADV dan driver PS4.
7. **No Hallucinated APIs:** Jangan membuat stub atau mengimplementasikan API yang belum tersedia di runtime tanpa bukti dukungan nyata dari `orbis-win` / OpenOrbis SDK.
8. **Zero Fabrication:** Jangan mengarang nama dependency, flag compiler, command CLI, environment variable, atau library yang belum diverifikasi di upstream.
9. **Pin Everything:** Semua dependency wajib dipin:
   - Base Docker image menggunakan versi + digest (`@sha256:...`).
   - Git submodule dipin pada commit hash spesifik.
   - SDK bundle, Wine, DXVK, dan Mesa dipin sebagai satu pasangan yang kompatibel dan diverifikasi dengan SHA-256 checksum.
   - Dilarang menggunakan tag `latest`.
10. **100% Dockerized Build:** Seluruh proses build, validasi, packaging PKG, dan host testing **wajib** berjalan di dalam Docker yang membungkus (*wraps*) pipeline build resmi `orbis-win`. Jangan mengharuskan instalasi compiler/SDK manual di mesin host.
11. **No Game Files or Trademarks in Repo:** Dilarang memasukkan executable game, `settings.exe`, file `.img`, save data, logo resmi, atau aset proprietary pihak ketiga ke dalam repositori Git. Gunakan nama dan karya seni *clean-room* `SOCCER13`.
12. **No Proprietary Blobs in Docker Image:** Dilarang memasukkan file game Windows, firmware dump PS4, atau modul proprietary console ke dalam Docker image. Modul/input yang hanya berasal dari console pengguna harus disuplai melalui *external bind mount* atau folder lokal yang tidak di-commit (`build/`), dengan pesan error yang jelas jika belum tersedia.
13. **Preserve Working Upstream Code:** Jangan menghapus konfigurasi, profile game referensi, atau patch upstream yang sudah terbukti bekerja di `orbis-win`.
14. **Incremental & Measurable Changes:** Lakukan perubahan kecil, terisolasi, dan terukur.
15. **Testable Milestones:** Setiap milestone/fase harus menghasilkan *deliverable* konkret yang dapat diverifikasi terhadap *acceptance criteria*.
16. **Host Tests Before Packaging:** Jalankan seluruh *host tests* di dalam Docker sebelum men-generate file `.pkg`.
17. **Hardware Truth Only:** Jangan pernah mengklaim game berhasil berjalan hanya karena proses Wine berhasil di-*spawn* atau container berhasil mem-build PKG. Status keberhasilan gameplay hanya sah setelah pengujian di hardware PS4 HEN target.
18. **Document Failures & Workarounds:** Setiap crash, kegagalan inisialisasi, ketidakcocokan shader/API, dan workaround yang diterapkan wajib didokumentasikan beserta bukti log-nya.

---

## 3. First Task for AI Agent (Phase 0 Gate)

Phase 0 telah diselesaikan dengan 5 deliverable dokumen di folder `docs/`:
1. `docs/REPOSITORY-AUDIT.md` — Analisis arsitektur aktual `orbis-win`, alur build upstream, struktur runtime, dan perbandingan dengan `futbol13`.
2. `docs/DEPENDENCY-MATRIX.md` — Inventaris lengkap seluruh dependency beserta versi/commit pin dan checksum.
3. `docs/PS4-COMPATIBILITY-ANALYSIS.md` — Evaluasi kapabilitas PS4 (CPU Jaguar, GPU GCN/RADV Vulkan, batas RAM, Orbis OS filesystem/permissions).
4. `docs/DOCKER-BUILD-PLAN.md` — Rancangan pembungkusan build script resmi `orbis-win` ke dalam multi-stage Docker container.
5. `docs/SOCCER13-COMPATIBILITY-PLAN.md` — Rencana integrasi spesifik `soccer13` (PE32, DXVK D3D9, XInput, format biner `settings.dat`).

---

## 4. Target Project Structure & Boundaries

Pertahankan pemisahan yang bersih antara upstream runtime, infrastruktur Docker, dan kode spesifik `soccer13`:

```text
soccer13/
├── docker/
│   ├── Dockerfile              # Pinned base image + build dependencies
│   ├── docker-compose.yml      # Service definitions & volume/bind mounts
│   ├── build-env.sh            # Environment & checksum verification
│   └── dependencies.lock       # Locked versions, commit hashes, SHA256
├── runtime/
│   └── orbis-win/              # Git submodule / upstream reference (JANGAN dimodifikasi sembarangan)
├── app/
│   ├── assets/                 # icon0.png, pic0.png, pic1.png, bg.raw
│   ├── launcher/               # Native PS4 Homebrew Launcher SOCCER13 (C/C++)
│   │   ├── src/
│   │   │   ├── handoff_stub.c  # Direct Autoboot Stub (no-RELRO)
│   │   │   ├── launcher_ui.c   # Model 1 Preset Selector
│   │   │   ├── launcher_video.c# Direct VideoOut PS4
│   │   │   └── main.c          # Launcher entrypoint
│   │   ├── include/
│   │   └── CMakeLists.txt
│   ├── profiles/
│   │   └── soccer13.profile    # Runtime & Wine environment profile untuk SOCCER13
│   └── config/
│       ├── dxvk.conf           # Konfigurasi DXVK D3D9 yang tervalidasi untuk RADV PS4
│       └── settings-template/  # Template settings.dat & registry untuk SOCCER13
├── scripts/
│   ├── build.sh                # Entrypoint: docker compose run --rm builder build
│   ├── test.sh                 # Entrypoint: docker compose run --rm builder test
│   ├── release.sh              # Entrypoint: docker compose run --rm builder release
│   ├── package.sh              # Pembuatan Standalone PKG (SOCCER13-FULL-PS4.pkg)
│   ├── dump-from-ps4.py        # Penarik dump game & registry dari PS4 via FTP
│   └── validate.sh             # Validasi artefak, lisensi, kebersihan merek dagang, dan SHA256
├── tests/
│   ├── launcher/               # Unit tests untuk logika launcher, path, & validator
│   ├── config/                 # Tests untuk generator/parser settings.dat & profile
│   ├── package/                # Verifikasi struktur PKG & tidak adanya file terlarang
│   └── integration/            # End-to-end host pipeline checks
├── docs/                       # Dokumentasi teknis & hasil audit
├── artifacts/                  # Output build di host (diabaikan oleh Git)
├── prd.md                      # Product Requirements Document (sumber kebenaran utama)
├── dump.md                     # Spesifikasi teknis dump & standalone packaging
├── AGENTS.md                   # Instruksi operasional AI Agent (dokumen ini)
└── README.md                   # Dokumentasi utama repositori
```

---

## 5. Development Phases & Current Status

| Phase | Fokus Utama | Deliverables Utama | Status |
|---|---|---|---|
| **Phase 0** | Repository Audit | 5 dokumen di `docs/` + Feasibility & Blocker Report | **COMPLETE** |
| **Phase 1** | Docker Build Infrastructure | `Dockerfile`, `docker-compose.yml`, `dependencies.lock`, `scripts/` | **COMPLETE** |
| **Phase 2** | Baseline Runtime | Baseline PKG, `BUILD-MANIFEST.txt`, verifikasi eksekusi | **COMPLETE** |
| **Phase 3** | SOCCER13 Integration | `soccer13.profile`, prefix setup, validator instalasi, generator `settings.dat`, `dxvk.conf` | **COMPLETE** |
| **Phase 4** | Game Compatibility | 12 tahap pengujian lulus di hardware PS4 target: Wine boot $\rightarrow$ Game boot $\rightarrow$ Main Menu $\rightarrow$ Match Load $\rightarrow$ Gameplay (1080p High 60 FPS) $\rightarrow$ Audio $\rightarrow$ Controller $\rightarrow$ Clean Exit. | **COMPLETE** |
| **Phase 5** | Launcher Integration | UI Native PS4 Launcher `SOCCER13` (Model 1 Preset Selector) & Direct Autoboot Stub (`handoff_stub.c`) | **COMPLETE** |
| **Phase 6** | Standalone Release | `scripts/dump-from-ps4.py`, Standalone `SOCCER13-FULL-PS4.pkg` (6.1 GB), penanganan error `2157510736`, patch PlayGo `PkgTool.Core`, dan verifikasi SHA-256. | **COMPLETE** |

---

## 6. Technical & Functional Guardrails

### 6.1 Docker CLI Contract
Seluruh workflow developer dijalankan melalui container:
```bash
docker compose build
docker compose run --rm builder build
docker compose run --rm builder test
docker compose run --rm builder release
docker compose run --rm builder clean
```
- Gunakan `set -euo pipefail` pada seluruh shell script agar build langsung berhenti (*fail-fast*) ketika ada tahap yang gagal.

### 6.2 Game Installation & Wine Prefix (FR-01, FR-02, FR-08)
- **Validasi Instalasi:** Pastikan keberadaan executable utama (`pes2013.exe`) dan direktori `img/` sebelum menyalin atau menjalankan game.
- **Sumber Instalasi:** Dukung pembacaan dari USB, FTP, dan internal bundle PKG tanpa memodifikasi file sumber dan tanpa mengunduh game dari internet.
- **Proteksi Save Data:** Lokasi save di dalam prefix (`drive_c/users/.../Documents/.../save/`) yang berisi `EDIT.bin`, Option File, dan Master League **tidak boleh ditimpa atau dihapus** saat melakukan proses *Repair* prefix atau update package.

### 6.3 Standalone PKG Packaging & Volume Type Integrity (Mandatory Guardrail)
- **Standalone Games Wajib Menggunakan `pkg_ps4_app`:**
  - **DILARANG** menggunakan `<volume_type>pkg_ps4_remaster</volume_type>` pada standalone package. `pkg_ps4_remaster` menetapkan `ContentType.DP` (Digital Package Update/Remaster). Pada PS4 HEN, GoldHEN Package Installer / BGFT akan menolak instalasi dengan error kode **`2157510736`** (`0x80990050` = `SCE_BGFT_ERROR_INVALID_SESSION`) jika base app belum ada.
  - Standalone game **wajib** menggunakan `<volume_type>pkg_ps4_app</volume_type>` (`ContentType.GD` / `0x0`).
- **Patch Otomatis PkgTool.Core (PlayGo Chunk Allocation Shortfall):**
  - Pada package besar (>2.2 GB), upstream `PkgTool.Core` memiliki bug buffer sizing di mana penambahan entry hash PlayGo menggeser `body_size` melewati batas alignment 512 KB, memicu exception `Playgo Chunk hash file was not allocated enough space`.
  - `scripts/package.sh` secara otomatis dan idempoten menerapkan patch 1-byte pada `PkgTool.Core` (offset IL `0x6583`, byte file `77934451`: `0x1a` $\rightarrow$ `0x1e` untuk mengalokasikan 8 byte per chunk pada pre-pass). Jangan mengubah kembali perbandingan `ble.s` ke `br.s` karena merusak keseimbangan evaluasi stack .NET JIT (`InvalidProgramException`).

### 6.4 Direct Autoboot Stub & no-RELRO Contract
- `app/launcher/src/handoff_stub.c` dikompilasi menggunakan flag `PW_EXECUTABLE_NO_RELRO=1` dan script linker `stub-no-relro.ld` dengan rentang data segment `[0x7fff0000, 0x80000000)`.
- Menggunakan pure libkernel syscalls (`sceKernelOpen`, `sceKernelRead`, `sceKernelWrite`, `sceKernelStat`, `sceKernelMkdir`, `sceKernelDebugOutText`).
- Menghasilkan `settings.dat` 852-byte kanonikal dengan checksum CRC-16/XMODEM NOT terbalik yang cocok dengan formula Konami sebelum memanggil relocation loader.

### 6.5 Security, Trademark & Clean-Room Hygiene (NFR-05)
- Gunakan nama **`SOCCER13` / `soccer13`** untuk seluruh artefak, UI, dan dokumentasi.
- **DILARANG KERAS** menulis IP address konsol asli (mis. `192.168.x.x`), kredensial FTP, atau path host absolut ke dalam file yang di-commit ke Git. Gunakan variabel lingkungan atau file `.env` (yang di-ignore oleh `.gitignore`).
- Semua unit test di `tests/package/test_clean_room.py` wajib lulus sebelum commit.

### 6.6 Patching & Modding Operational Rules
- **Aset Dump Bersifat Lokal & Persisten:**
  - File hasil dump game dari PS4 tersimpan di `build/ps4-dump/game/SOCCER13/` dan `build/ps4-dump/seed/`.
  - Folder `build/` sepenuhnya di-ignore oleh Git, menjaga kebersihan repositori.
- **Pemasangan Patch Baru:**
  1. *Option File / Transfer (`EDIT.bin`):* Cukup dikirim langsung via FTP ke `/data/prospero-win/prefixes/soccer13/drive_c/users/.../save/EDIT.bin`. Tidak perlu rebuild PKG dan tidak perlu dump ulang.
  2. *Testing Mod Langsung di PS4:* File mod baru dapat dikirim via FTP langsung ke `/data/prospero-win/prefixes/soccer13/drive_c/Games/SOCCER13/`.
  3. *Repackage Standalone PKG Baru:* Cukup letakkan file patch baru di `build/ps4-dump/game/SOCCER13/` pada PC, lalu jalankan `docker compose run --rm builder ./scripts/package.sh`. **Tidak perlu melakukan dump ulang dari konsol.**
