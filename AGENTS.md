# AGENTS.md — AI Coding Agent Instructions & Operational Guide

**Project:** `soccer13` (SOCCER13 PC → PS4 HEN)  
**Type:** Windows PC Game Compatibility Port  
**Target Platform:** PlayStation 4 (PS4 HEN)  
**Base Runtime:** [`plastikman/orbis-win`](https://github.com/plastikman/orbis-win)  
**Reference Implementation:** [`7tg/futbol13`](https://github.com/7tg/futbol13)  
**Primary Specification:** [prd.md](./prd.md)

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
   - **Native PS4 Homebrew Launcher (`SOCCER13`)** untuk manajemen instalasi, Wine prefix, konfigurasi `settings.dat`, input DualShock 4, dan logging

Setiap AI Coding Agent yang bekerja di repositori ini **wajib** mematuhi seluruh aturan, batasan arsitektur, dan tahapan kerja di dokumen ini sebelum menulis atau memodifikasi kode.

---

## 2. Mandatory Rules (Golden Rules)

AI Coding Agent **harus** mematuhi 18 aturan utama berikut tanpa pengecualian:

1. **Audit First:** Jangan langsung menulis implementasi launcher, script build, atau mengubah runtime sebelum menyelesaikan **Phase 0: Repository Audit**.
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
12. **No Proprietary Blobs in Docker Image:** Dilarang memasukkan file game Windows, firmware dump PS4, atau modul proprietary console ke dalam Docker image. Modul/input yang hanya berasal dari console pengguna harus disuplai melalui *external bind mount* yang tidak di-commit, dengan pesan error yang jelas jika belum tersedia.
13. **Preserve Working Upstream Code:** Jangan menghapus konfigurasi, profile game referensi, atau patch upstream yang sudah terbukti bekerja di `orbis-win`.
14. **Incremental & Measurable Changes:** Lakukan perubahan kecil, terisolasi, dan terukur.
15. **Testable Milestones:** Setiap milestone/fase harus menghasilkan *deliverable* konkret yang dapat diverifikasi terhadap *acceptance criteria*.
16. **Host Tests Before Packaging:** Jalankan seluruh *host tests* di dalam Docker sebelum men-generate file `.pkg`.
17. **Hardware Truth Only:** Jangan pernah mengklaim game berhasil berjalan hanya karena proses Wine berhasil di-*spawn* atau container berhasil mem-build PKG. Status keberhasilan gameplay hanya sah setelah pengujian di hardware PS4 HEN target.
18. **Document Failures & Workarounds:** Setiap crash, kegagalan inisialisasi, ketidakcocokan shader/API, dan workaround yang diterapkan wajib didokumentasikan beserta bukti log-nya.

---

## 3. First Task for AI Agent (Phase 0 Gate)

**STOP & CHECK:** Sebelum menulis kode di `app/`, `docker/`, atau `scripts/`, periksa apakah 5 dokumen audit Phase 0 berikut sudah ada dan lengkap. Jika belum, **tugas pertama Anda adalah menyelesaikan Phase 0: Repository Audit**.

### Target Audit Upstream (`orbis-win` & `futbol13`)
Agent harus mengaudit secara faktual:
- `docs/BUILDING.md`, `HARDWARE-STATUS.md`, dan `AGENTS.md` milik `orbis-win`
- `scripts/` dan `scripts/ci/` di `orbis-win`
- `config.env.example` dan mekanisme fetching SDK
- Persyaratan modul console (file/library apa yang perlu diekstrak dari PS4 pengguna)
- Commit hash pin saat ini untuk Wine, DXVK, Mesa/RADV, dan OpenOrbis toolchain
- Wine ABI yang digunakan serta game profile referensi yang sudah terbukti berjalan di `orbis-win`
- Pola game profile, Wine prefix setup, `settings.dat`, dan launcher workflow dari `7tg/futbol13`

### 5 Dokumen Deliverable Wajib Phase 0
1. `docs/REPOSITORY-AUDIT.md` — Analisis arsitektur aktual `orbis-win`, alur build upstream, struktur runtime, dan perbandingan dengan `futbol13`.
2. `docs/DEPENDENCY-MATRIX.md` — Inventaris lengkap seluruh dependency (SDK, compiler, Wine, DXVK, Mesa/RADV, host tools, dan console modules yang tidak boleh didistribusikan) beserta versi/commit pin dan checksum.
3. `docs/PS4-COMPATIBILITY-ANALYSIS.md` — Evaluasi kapabilitas PS4 (CPU Jaguar, GPU GCN/RADV Vulkan, batas RAM, Orbis OS filesystem/permissions) serta perbedaan antara PS4 Fat, Slim, dan Pro.
4. `docs/DOCKER-BUILD-PLAN.md` — Rancangan pembungkusan (*wrapping*) build script resmi `orbis-win` ke dalam multi-stage Docker container, strategi caching volume, dan external bind mount.
5. `docs/SOCCER13-COMPATIBILITY-PLAN.md` — Rencana integrasi spesifik `soccer13` (validasi executable PE32, kebutuhan DLL/Win32 API, Direct3D 9 → DXVK, XInput mapping, DirectSound/XAudio, struktur registry, dan format biner `settings.dat`).

> **Gate Condition:** Setelah kelima dokumen di atas selesai dibuat, berikan **Feasibility Report** dan **Daftar Blocker** kepada pengguna sebelum melanjutkan ke Phase 1.

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
│   ├── launcher/               # Native PS4 Homebrew Launcher SOCCER13 (C/C++)
│   │   ├── src/
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
│   ├── package.sh              # Pembuatan PS4 PKG (SOCCER13-PS4.pkg)
│   └── validate.sh             # Validasi artefak, lisensi, kebersihan merek dagang, dan SHA256
├── tests/
│   ├── launcher/               # Unit tests untuk logika launcher, path, & validator
│   ├── config/                 # Tests untuk generator/parser settings.dat & profile
│   ├── package/                # Verifikasi struktur PKG & tidak adanya file terlarang
│   └── integration/            # End-to-end host pipeline checks
├── docs/                       # Dokumentasi teknis & hasil audit Phase 0
├── artifacts/                  # Output build di host (diabaikan oleh Git)
├── prd.md                      # Product Requirements Document (sumber kebenaran utama)
├── AGENTS.md                   # Instruksi operasional AI Agent (dokumen ini)
└── README.md                   # Dokumentasi utama repositori
```

---

## 5. Development Phases & Acceptance Gates

Kerjakan project secara berurutan dari **Phase 0** hingga **Phase 6**. Jangan melompati fase.

| Phase | Fokus Utama | Deliverables Utama | Gate / Acceptance Criteria |
|---|---|---|---|
| **Phase 0** | Repository Audit | 5 dokumen di `docs/` + Feasibility & Blocker Report | Semua dependency, commit pin, dan alur build upstream `orbis-win` terpetakan tanpa asumsi. |
| **Phase 1** | Docker Build Infrastructure | `Dockerfile`, `docker-compose.yml`, `dependencies.lock`, `scripts/` | Image ter-build dari clean checkout tanpa bergantung pada toolchain host; validasi checksum berjalan. |
| **Phase 2** | Baseline Runtime | Baseline PKG, `BUILD-MANIFEST.txt`, laporan uji PS4 | `orbis-win` baseline berjalan di PS4 HEN target, Wine terinisialisasi, dan game referensi upstream mencapai gameplay. |
| **Phase 3** | SOCCER13 Integration | `soccer13.profile`, prefix setup, validator instalasi, generator `settings.dat`, `dxvk.conf` | Prefix `soccer13` siap, executable & `img/` tervalidasi, konfigurasi terpasang tanpa mengubah file sumber pengguna. |
| **Phase 4** | Game Compatibility | Compatibility matrix, tuning DXVK/XInput/Audio, laporan performa | 12 tahap pengujian lulus di PS4: Wine boot → Game boot → Init → Main Menu → Team Select → Match Load → Gameplay → Audio → Controller → Match End → Save/Load → Clean Exit. |
| **Phase 5** | Launcher Integration | Aplikasi Native PS4 Launcher `SOCCER13` (`app/launcher/`), UI DualShock 4, fitur Repair & Backup Save | Seluruh menu dinavigasi dengan DualShock 4 (tanpa keyboard/mouse), status/error jelas, Repair tidak menghapus save data. |
| **Phase 6** | Release | `release/SOCCER13-PS4.pkg`, `BUILD-MANIFEST.txt`, `SHA256SUMS`, `THIRD_PARTY.md`, `README.md` | PKG terinstal di PS4 HEN, game berjalan dari launcher `SOCCER13`, bebas file/merek dagang proprietary, audit lisensi & SHA-256 lulus. |

---

## 6. Technical & Functional Guardrails

### 6.1 Docker CLI Contract
Implementasikan dan pertahankan antarmuka perintah berikut untuk seluruh workflow developer:
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
- **Sumber Instalasi:** Dukung pembacaan dari USB dan FTP tanpa memodifikasi file sumber dan tanpa mengunduh game dari internet.
- **Proteksi Save Data:** Lokasi save di dalam prefix (`drive_c/users/.../Documents/.../save/`) yang berisi `EDIT.bin`, Option File, dan Master League **tidak boleh ditimpa atau dihapus** saat melakukan proses *Repair* prefix.

### 6.3 Game Configuration & Launching (FR-03, FR-04, FR-07)
- **Tanpa `settings.exe` di PS4:** Konfigurasi dilakukan langsung oleh launcher `SOCCER13` dengan men-generate/memodifikasi `settings.dat` menggunakan struktur biner yang telah diverifikasi.
- **Baseline Konfigurasi Pengujian:**
  - Mode: Fullscreen
  - Resolusi awal: `1280x720` (jangan memaksakan `1600x900` atau `1920x1080` sebelum `720p` terbukti stabil mencapai gameplay)
  - Graphics Quality: Medium
  - Controller: XInput
  - Audio: Enabled (uji terpisah dari grafis)
  - VSync: Configurable
- **Deteksi Status Proses:** Launcher tidak boleh menandai eksekusi sebagai "berhasil" hanya karena `fork`/`exec` Wine berhasil; pantau lifecycle proses hingga game berjalan dan tangkap exit code serta log crash.

### 6.4 Security, Trademark & Clean-Room Hygiene (NFR-05)
- Gunakan nama **`SOCCER13` / `soccer13`** untuk seluruh artefak, UI, dan dokumentasi.
- Jangan pernah menulis IP address PS4, kredensial FTP, atau path lokal spesifik developer ke dalam file yang di-commit (gunakan file `.env` yang masuk ke `.gitignore`).
- Tambahkan pemeriksaan otomatis di `scripts/validate.sh` dan `tests/package/` untuk memastikan tidak ada file `.exe`, `.dll` proprietary, `.img` aset game, atau dump firmware PS4 yang ikut terkemas di dalam `.pkg` maupun repositori.

### 6.5 Hardware Testing Recording Standard (Section 9.2)
Setiap laporan pengujian pada konsol PS4 wajib mencantumkan metadata berikut:
- **PS4 Model:** Fat / Slim / Pro (hasil di PS4 Pro tidak boleh diasumsikan otomatis berlaku di Fat/Slim)
- **System Firmware Version:** (mis. 9.00 / 11.00)
- **HEN Version:** (mis. GoldHEN version)
- **Package Version & Commit SHA:**
- **Game Edition:** (versi rilis/patch executable pengguna)
- **Runtime ABI:**
- **Test Result per Stage (1–12):** PASS / FAIL
- **Log File Path:** Lokasi log yang diambil via USB/FTP
