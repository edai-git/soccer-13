# PRODUCT REQUIREMENTS DOCUMENT (PRD)
# SOCCER13 PC → PS4 HEN (`soccer13`)

**Project codename:** `soccer13` (SOCCER13 Orbis Port)  
**Project type:** Windows PC Game Compatibility Port  
**Target platform:** PlayStation 4 (PS4 HEN)  
**Base runtime:** [plastikman/orbis-win](https://github.com/plastikman/orbis-win)  
**Reference implementation:** [7tg/futbol13](https://github.com/7tg/futbol13)  
**Build environment:** Docker  
**Primary language:** C / C++  
**Build target:** Native PS4 Homebrew PKG (`SOCCER13-PS4.pkg`)  
**Project status:** Initial specification

---

# 1. PROJECT OVERVIEW

## 1.1 Background

Project **SOCCER13** (`soccer13`) bertujuan menjalankan game sepak bola klasik tahun 2013 versi Windows PC milik pengguna pada PlayStation 4 yang menggunakan HEN, dengan menggunakan penamaan netral **`soccer13` / `SOCCER13`** agar bebas dari merek dagang/hak cipta pihak ketiga.

Project mengadopsi pendekatan compatibility layer, bukan melakukan porting ulang seluruh source code game.

Konsep utama adalah menjalankan executable Windows asli menggunakan Wine yang telah diadaptasi untuk lingkungan PS4.

Referensi utama adalah `FUTBOL13`, sebuah implementasi serupa pada PS5 menggunakan:
- Wine
- DXVK
- Vulkan
- Mesa
- Native console launcher

Untuk implementasi PS4, project `soccer13` akan menggunakan `orbis-win` sebagai fondasi runtime dan platform compatibility.

## 1.2 Main Goal

Membuat aplikasi homebrew PS4 (`SOCCER13`) yang mampu:

1. Menjalankan executable game PC asli (`pes2013.exe`).
2. Membaca folder instalasi game PC milik pengguna.
3. Menggunakan compatibility layer Wine.
4. Menjalankan rendering DirectX melalui backend grafis yang tersedia pada PS4.
5. Mendukung DualShock 4.
6. Menghasilkan aplikasi dalam format PKG (`SOCCER13-PS4.pkg`).
7. Melakukan build secara reproducible menggunakan Docker.

## 1.3 Core Concept

**Do not rebuild the game. Run the original Windows game through a PS4-compatible runtime (`soccer13`).**

Project tidak bertujuan membuat ulang gameplay, model pemain, stadion, animasi, atau physics game.

Aplikasi tetap menggunakan executable dan aset asli milik pengguna tanpa menyertakan file berhak cipta ke dalam repositori maupun paket rilis.

---

# 2. TECHNICAL ARCHITECTURE

## 2.1 High-Level Architecture

```text
              WINDOWS PC GAME
                     |
               SOCCER13 PC
                     |
        +------------+------------+
        |                         |
        v                         v
   Game EXE                    img/
   (PE32 Binary)            Game Assets
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
             SOCCER13 GAMEPLAY
```

Catatan arsitektur:

- Wine menangani Windows API.
- DXVK menjadi kandidat penerjemah Direct3D 9 ke Vulkan.
- Mesa/RADV menyediakan backend grafis AMD.
- `orbis-win` menyediakan adaptasi runtime untuk Orbis OS.
- Native launcher `SOCCER13` mengatur instalasi, konfigurasi, dan eksekusi game.

DXVK harus divalidasi terhadap konfigurasi runtime dan driver PS4. Jangan mengasumsikan semua fitur Vulkan tersedia.

## 2.2 Main Components

### A. orbis-win Runtime

Repository:

https://github.com/plastikman/orbis-win

Bertanggung jawab untuk:

- Windows compatibility runtime.
- Wine integration.
- CPU execution backend.
- Memory management.
- Windows API compatibility.
- Mesa/RADV integration.
- Graphics runtime.
- Audio runtime.
- Native PS4 integration.

Ketentuan:

Jadikan `orbis-win` sebagai upstream/foundation. Hindari mengganti implementasi runtime yang sudah stabil hanya untuk membuat `soccer13` berjalan.

### B. Wine

Bertanggung jawab menjalankan executable Windows.

Target:
- Windows PE32 executable.
- Win32 API.
- Windows registry.
- Windows filesystem.
- XInput.
- DirectInput jika diperlukan.

### C. DXVK

Bertanggung jawab menerjemahkan Direct3D 9 menjadi Vulkan.

Target:
- Direct3D 9.
- Shader translation.
- Texture management.
- Render state.
- Presentation.
- Frame synchronization.

Versi DXVK harus dipin dan divalidasi dengan driver Vulkan yang digunakan.

### D. Mesa / RADV

Bertanggung jawab pada GPU rendering backend.

Target:
- AMD GPU support.
- Vulkan implementation.
- Memory allocation.
- Command submission.
- Display integration.

Gunakan versi Mesa dan SDK yang kompatibel dengan baseline `orbis-win`.

### E. Native Launcher (`SOCCER13`)

Aplikasi native PS4 yang bertanggung jawab untuk:

- Menampilkan menu `SOCCER13`.
- Mengelola instalasi game.
- Membuat atau memvalidasi Wine prefix `soccer13`.
- Mengatur resolusi.
- Mengatur controller.
- Menjalankan game.
- Mengelola proses game.
- Menampilkan log dan status error.

---

# 3. FUNCTIONAL REQUIREMENTS

## FR-01: Game Installation

Aplikasi harus dapat menerima folder instalasi game PC milik pengguna.

Struktur minimal:

```text
SOCCER13/
├── pes2013.exe
├── img/
├── settings.exe
└── additional game files/
```

Ketentuan:

- Memvalidasi keberadaan executable utama (`pes2013.exe`).
- Memvalidasi folder `img/`.
- Menghitung ukuran instalasi.
- Memeriksa file yang dibutuhkan.
- Mendukung instalasi melalui USB.
- Mendukung instalasi melalui FTP.
- Menyalin game ke Wine prefix `soccer13`.
- Tidak mengubah file instalasi sumber.
- Tidak mengunduh game dari internet.

## FR-02: Wine Prefix Management

Aplikasi harus mendukung Wine prefix khusus `soccer13`.

Contoh:

```text
/data/orbis-win/
└── prefixes/
    └── soccer13/
        ├── drive_c/
        │   ├── Program Files/
        │   └── users/
        ├── dosdevices/
        └── system.reg
```

Ketentuan:

- Prefix dibuat di PC atau konsol melalui workflow yang kompatibel.
- Prefix harus menggunakan ABI/runtime yang sesuai.
- Game dapat dijalankan melalui profil khusus (`soccer13.profile`).
- Mendukung repair dan validasi prefix.
- Tidak menghapus save game saat repair.

## FR-03: Game Configuration

Aplikasi harus menyediakan konfigurasi `soccer13` tanpa harus menjalankan `settings.exe` di PS4.

Konfigurasi awal:

- Fullscreen.
- Resolusi 1280×720.
- Graphics quality: Medium.
- Controller: XInput.
- Audio enabled.
- VSync configurable.

Nilai tersebut merupakan konfigurasi awal untuk pengujian, bukan klaim bahwa seluruh opsi pasti didukung.

Aplikasi harus dapat membuat atau mengubah `settings.dat` menggunakan format yang sudah diverifikasi.

## FR-04: Game Launching

Aplikasi harus dapat:

1. Memeriksa game installation.
2. Memeriksa Wine prefix `soccer13`.
3. Memeriksa runtime dependencies.
4. Memuat profil `soccer13`.
5. Mengatur environment variables.
6. Menjalankan executable game.
7. Mendeteksi proses selesai.
8. Kembali ke launcher.

Launcher tidak boleh menganggap game berhasil hanya karena proses Wine berhasil dibuat. Status keberhasilan harus didasarkan pada hasil eksekusi game.

## FR-05: Controller Support

Target utama adalah DualShock 4.

Mapping awal:

| PS4 Controller | SOCCER13 Action |
|---|---|
| D-Pad | Movement |
| Left Stick | Player movement |
| Cross | Pass |
| Circle | Cross / Sliding tackle |
| Square | Shoot |
| Triangle | Through pass |
| L1 | Player switch |
| L2 | Special control |
| R1 | Sprint |
| R2 | Modifier |
| Options | Pause |

Mapping harus dapat disesuaikan melalui profil input.

Jika game hanya mendeteksi XInput, gunakan mapping yang sesuai dengan kemampuan runtime `orbis-win`.

## FR-06: Audio

Aplikasi harus mendukung:

- Background music.
- Commentary.
- Stadium sounds.
- Match effects.
- Menu sounds.

Prioritaskan DirectSound/XAudio compatibility sesuai API yang benar-benar digunakan oleh game.

Audio harus diuji terpisah dari rendering.

## FR-07: Resolution Management

Pilihan resolusi awal:

- 1280×720
- 1600×900
- 1920×1080

Resolusi native rendering dan output display harus diuji secara terpisah.

Jangan memaksakan 1080p sebelum kestabilan gameplay terbukti.

## FR-08: Save Data

Game harus mempertahankan save data pengguna pada path `save/` di dalam `Documents/` prefix Wine.

Ketentuan:

- Import save dari PC.
- Mempertahankan EDIT file.
- Mempertahankan Master League.
- Mempertahankan option file.
- Tidak menimpa save saat repair.
- Mendukung backup dan restore.

## FR-09: Logging

Sistem harus menyediakan logging untuk:

- Launcher startup.
- Prefix validation.
- Wine initialization.
- Game process startup.
- Graphics initialization.
- Audio initialization.
- Controller initialization.
- Game exit.
- Crash/error.

Log harus dapat diambil melalui USB atau FTP.

---

# 4. APPLICATION UI

## 4.1 Main Menu

Launcher harus memiliki tampilan sederhana dan berorientasi controller dengan identitas netral **`SOCCER13`** (tanpa menggunakan logo atau merek dagang pihak ketiga).

Menu utama:

```text
+--------------------------------------+
|                                      |
|              SOCCER13                |
|                                      |
|          [ CUSTOM COVER ]            |
|                                      |
|            GAME STATUS               |
|                                      |
|             [ PLAY ]                 |
|             [ SETTINGS ]             |
|             [ REPAIR ]               |
|             [ ABOUT ]                |
|                                      |
+--------------------------------------+
```

## 4.2 Settings

Pengaturan:

- Resolution.
- Graphics quality.
- VSync.
- Controller profile.
- Audio.
- Performance overlay.
- Logging.

## 4.3 Game Status

Status yang ditampilkan:

- Game installed.
- Game not found.
- Prefix valid.
- Runtime ready.
- Missing dependencies.
- Game running.
- Game exited.
- Game crashed.

## 4.4 Navigation

Semua menu harus bisa dioperasikan menggunakan DualShock 4.

Tidak boleh bergantung pada keyboard atau mouse untuk operasi normal.

---

# 5. DOCKER BUILD SYSTEM

## 5.1 Objective

Seluruh proses build harus berjalan melalui Docker.

Developer tidak perlu menginstal compiler, SDK, Wine build dependencies, Mesa build dependencies, atau packaging tools secara manual pada host.

Host hanya memerlukan:

- Docker Engine / Docker Desktop.
- Git.
- Shell.
- Ruang penyimpanan yang memadai.

Build host yang direkomendasikan adalah Linux x86-64 atau Windows dengan WSL2 dan Docker Desktop.

## 5.2 Docker Responsibilities

Docker harus mengelola:

- Build dependencies.
- Clang / LLVM.
- CMake.
- Ninja.
- OpenOrbis-compatible toolchain.
- Wine build environment.
- Mesa build dependencies.
- DXVK build dependencies.
- Native launcher compilation.
- PS4 package generation.
- Artifact validation.

SDK, header, library, dan Mesa harus menggunakan versi yang kompatibel sebagai satu pasangan. Jangan mencampur SDK bundle dari versi berbeda.

## 5.3 Docker Architecture

```text
HOST MACHINE
    |
    v
Docker CLI
    |
    v
Docker Image
    |
    +----------------------+
    |                      |
    v                      v
Build Dependencies    Pinned SDK Bundle
    |                      |
    +-----------+----------+
                |
                v
          Source Checkout
                |
                v
          Build Pipeline
                |
     +----------+----------+
     |          |          |
     v          v          v
   Wine       Mesa       Launcher
     |          |          |
     +----------+----------+
                |
                v
           PS4 Modules
                |
                v
           Package PKG
                |
                v
          Validation
                |
                v
         HOST ARTIFACTS
```

## 5.4 Docker Commands

Target developer workflow:

```bash
# Build Docker image
docker compose build

# Build complete project
docker compose run --rm builder build

# Run tests
docker compose run --rm builder test

# Build release package
docker compose run --rm builder release

# Clean build artifacts
docker compose run --rm builder clean
```

Perintah tersebut merupakan interface yang harus diimplementasikan, bukan perintah yang diasumsikan sudah tersedia di upstream.

## 5.5 Docker Requirements

- Gunakan multi-stage Docker build jika bermanfaat.
- Pin base image menggunakan versi dan digest.
- Pin seluruh dependencies.
- Verifikasi checksum SDK.
- Gunakan Git submodule pada commit tertentu.
- Jangan menggunakan `latest` untuk dependency release.
- Gunakan persistent volume untuk build cache.
- Simpan hasil build pada folder host.
- Build harus berhenti jika salah satu tahap gagal.
- Jangan memasukkan game files atau Windows executable proprietary ke dalam image.
- Jangan memasukkan firmware dump atau module proprietary console ke image.
- Input khusus console harus diberikan melalui external bind mount yang tidak di-commit.

## 5.6 Important Build Constraint

Repository `orbis-win` saat ini memiliki build workflow dan script sendiri.

Implementasi Docker harus membungkus build pipeline resmi repository tersebut, bukan membuat ulang seluruh proses build dengan asumsi dependency yang belum diverifikasi.

AI developer harus terlebih dahulu mengaudit:

- `docs/BUILDING.md`
- `scripts/`
- `scripts/ci/`
- `config.env.example`
- SDK fetching scripts
- Console module requirements
- Current upstream commit pins

Jika suatu dependency atau module hanya dapat disediakan dari console milik pengguna, build harus meminta input tersebut melalui external mount dan memberikan error yang jelas jika tidak tersedia.

---

# 6. PROJECT STRUCTURE

Struktur target project `soccer13`:

```text
soccer13/
│
├── docker/
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── build-env.sh
│   └── dependencies.lock
│
├── runtime/
│   └── orbis-win/
│       └── upstream reference / integration
│
├── app/
│   ├── launcher/
│   │   ├── src/
│   │   ├── include/
│   │   └── CMakeLists.txt
│   │
│   ├── profiles/
│   │   └── soccer13.profile
│   │
│   └── config/
│       ├── dxvk.conf
│       └── settings-template/
│
├── scripts/
│   ├── build.sh
│   ├── test.sh
│   ├── release.sh
│   ├── package.sh
│   └── validate.sh
│
├── tests/
│   ├── launcher/
│   ├── config/
│   ├── package/
│   └── integration/
│
├── docs/
│   ├── ARCHITECTURE.md
│   ├── BUILDING.md
│   ├── INSTALLATION.md
│   ├── TROUBLESHOOTING.md
│   └── COMPATIBILITY.md
│
├── artifacts/
│
├── .gitmodules
├── .gitignore
├── docker-compose.yml
├── Makefile
└── README.md
```

Struktur ini adalah struktur project integrasi yang diusulkan. Jangan menyalin atau memindahkan seluruh repository upstream secara membabi buta. Pertahankan batas antara kode upstream, patch PS4, dan kode khusus `soccer13`.

---

# 7. DEVELOPMENT PHASES

## Phase 0 — Repository Audit

Tujuan: memahami kondisi aktual `orbis-win` sebelum melakukan modifikasi.

Pekerjaan:

- Clone repository.
- Clone submodules.
- Audit build scripts.
- Identifikasi SDK requirements.
- Identifikasi firmware dependencies.
- Identifikasi Wine ABI.
- Identifikasi DXVK version.
- Identifikasi Mesa/RADV version.
- Pelajari profile game yang sudah berhasil.
- Identifikasi dependency yang tidak dapat didistribusikan.

Deliverables:

- Architecture analysis (`docs/REPOSITORY-AUDIT.md`).
- Dependency inventory (`docs/DEPENDENCY-MATRIX.md`).
- PS4 compatibility report (`docs/PS4-COMPATIBILITY-ANALYSIS.md`).
- Docker implementation plan (`docs/DOCKER-BUILD-PLAN.md`).
- Game compatibility plan (`docs/SOCCER13-COMPATIBILITY-PLAN.md`).

Acceptance criteria:

- Seluruh dependency utama teridentifikasi.
- Build pipeline upstream dipahami.
- Tidak ada asumsi tentang kemampuan runtime yang belum terbukti.

## Phase 1 — Docker Build Infrastructure

Tujuan: membuat lingkungan build yang reproducible.

Pekerjaan:

- Membuat Dockerfile.
- Membuat docker-compose.yml.
- Membuat build entrypoint.
- Memasang dependency.
- Mengunduh SDK yang dipin.
- Memvalidasi checksum.
- Mengintegrasikan build script `orbis-win`.
- Menghasilkan build manifest.

Deliverables:

- Docker image.
- Build scripts.
- Dependency lock.
- Build documentation.

Acceptance criteria:

- Docker image berhasil dibuat.
- Build dapat dijalankan dari clean checkout.
- Build tidak bergantung pada compiler host.
- Error dependency dapat didiagnosis.

## Phase 2 — Baseline Runtime

Tujuan: membuktikan `orbis-win` berjalan pada PS4 target.

Pekerjaan:

- Build baseline runtime.
- Generate PS4 PKG.
- Validasi package.
- Instalasi pada PS4 HEN.
- Jalankan salah satu game Windows yang sudah terbukti kompatibel.
- Rekam log dan hasil pengujian.

Deliverables:

- Baseline PKG.
- Build manifest.
- Test report.

Acceptance criteria:

- Runtime berhasil berjalan di PS4 target.
- Launcher dapat dibuka.
- Wine berhasil diinisialisasi.
- Game referensi mencapai gameplay.

## Phase 3 — SOCCER13 Integration

Tujuan: menambahkan `soccer13` sebagai game profile.

Pekerjaan:

- Buat `soccer13.profile`.
- Identifikasi executable 32-bit.
- Validasi kebutuhan Windows API.
- Siapkan Wine prefix `soccer13`.
- Validasi registry.
- Validasi product code dari instalasi pengguna.
- Validasi `settings.dat`.
- Konfigurasi DXVK.
- Konfigurasi input XInput.

Deliverables:

- `soccer13` game profile.
- Prefix setup procedure.
- Game installation validator.
- Runtime configuration.

Acceptance criteria:

- Prefix berhasil disiapkan.
- Executable terdeteksi.
- Dependency utama tersedia.
- Game dapat dicoba dijalankan tanpa mengubah instalasi asli.

## Phase 4 — Game Compatibility

Tujuan: membuat `soccer13` mencapai gameplay.

Pengujian bertahap:

1. Wine startup.
2. Game process startup.
3. Game initialization.
4. Main menu.
5. Team selection.
6. Match loading.
7. Gameplay.
8. Audio.
9. Controller.
10. Match completion.
11. Save/load.
12. Game exit.

Setiap kegagalan harus memiliki log dan diagnosis.

Deliverables:

- Compatibility matrix.
- DXVK configuration.
- Input profile.
- Performance report.
- Known issues.

Acceptance criteria:

- Game mencapai main menu.
- Game dapat memulai pertandingan.
- Rendering berjalan stabil.
- Input controller berfungsi.
- Game dapat menyelesaikan pertandingan.
- Game dapat keluar tanpa merusak runtime.

## Phase 5 — Launcher Integration

Tujuan: menyediakan pengalaman aplikasi homebrew `SOCCER13` yang mudah digunakan.

Fitur:

- `SOCCER13` installation page.
- Game validation.
- Install / Repair.
- Play.
- Resolution settings.
- Controller configuration.
- Performance overlay.
- Logging.
- Save backup.

Deliverables:

- Native PS4 launcher.
- Custom clean-room UI assets (bebas merek dagang/hak cipta pihak ketiga).
- Configuration manager.
- Installation workflow.

Acceptance criteria:

- Semua navigasi menggunakan DualShock 4.
- Game dapat dijalankan dari launcher.
- Status game dan error terlihat jelas.
- Repair tidak menghapus save.

## Phase 6 — Release

Tujuan: menghasilkan package yang dapat diinstal pada PS4 HEN.

Pekerjaan:

- Final build.
- PKG validation.
- License audit.
- Dependency audit.
- Artifact checksum.
- Documentation.
- Hardware validation.

Deliverables:

```text
release/
├── SOCCER13-PS4.pkg
├── BUILD-MANIFEST.txt
├── SHA256SUMS
├── THIRD_PARTY.md
└── README.md
```

Acceptance criteria:

- PKG berhasil diinstal pada target PS4.
- Game dapat dijalankan dari Home Screen atau launcher.
- Tidak ada game executable, logo/merek dagang, atau aset proprietary yang dibundel.
- Seluruh dependency dan lisensi dicatat.

---

# 8. NON-FUNCTIONAL REQUIREMENTS

## NFR-01: Performance

Target awal:

- 1280×720.
- Target 60 FPS jika hardware dan compatibility runtime memungkinkan.
- Frame pacing stabil.
- Tidak terjadi memory exhaustion.
- Loading time dapat diukur.

60 FPS adalah target pengujian, bukan jaminan.

## NFR-02: Stability

- Tidak crash saat navigasi menu.
- Tidak crash saat memulai pertandingan.
- Tidak crash saat pergantian pemain.
- Tidak crash saat pertandingan selesai.
- Tidak merusak save data.

## NFR-03: Reproducibility

- Semua dependency dipin.
- Docker build konsisten.
- Build manifest mencatat commit dan dependency versions.
- Setiap package memiliki SHA-256.
- Tidak menggunakan dependency yang tidak terlacak.

## NFR-04: Maintainability

- Pisahkan upstream runtime dengan patch khusus `soccer13`.
- Gunakan konfigurasi game profile.
- Jangan hardcode lokasi instalasi.
- Dokumentasikan setiap workaround.
- Pertahankan known-good baseline.

## NFR-05: Security & Trademark Hygiene

- Gunakan nama **`soccer13` / `SOCCER13`** untuk seluruh penamaan paket, UI launcher, profil, dan aset seni agar tidak melanggar merek dagang atau hak cipta.
- Tidak menyertakan kredensial atau IP console dalam repository.
- Tidak mengunduh executable game.
- Tidak memodifikasi file game pengguna.
- Tidak menyertakan firmware proprietary.
- Validasi input path dan file.

---

# 9. TESTING STRATEGY

## 9.1 Host Tests

Semua test yang memungkinkan harus dijalankan di Docker tanpa membutuhkan PS4.

| Test | Target |
|---|---|
| Docker build | PASS |
| Dependency verification | PASS |
| Profile validation | PASS |
| Launcher unit tests | PASS |
| Configuration validation | PASS |
| Package validation | PASS |
| License & trademark audit | PASS |
| SHA-256 generation | PASS |

## 9.2 PS4 Hardware Tests

| Test | Target |
|---|---|
| PKG installation | PASS |
| Launcher startup | PASS |
| Wine startup | PASS |
| Game process startup | PASS |
| Main menu | PASS |
| Match loading | PASS |
| Gameplay | PASS |
| Audio | PASS |
| Controller | PASS |
| Save/load | PASS |
| Exit to launcher | PASS |

Setiap pengujian hardware wajib mencatat:

- PS4 model.
- Firmware.
- HEN version.
- Package version.
- Game edition.
- Runtime ABI.
- Test result.
- Log location.

Jangan menganggap hasil PS4 Pro otomatis berlaku pada PS4 Slim atau PS4 Fat.

---

# 10. RISKS AND MITIGATION

| Risiko | Mitigasi |
|---|---|
| Game tidak kompatibel dengan Wine | Analisis log dan Windows API dependencies |
| DirectX 9 tidak bekerja | Uji DXVK dan backend alternatif yang tersedia |
| Vulkan feature tidak tersedia | Audit kemampuan RADV |
| RAM terbatas | Optimasi memory dan resolution |
| Shader compilation lambat | Cache dan profiling |
| Controller tidak terdeteksi | Validasi XInput dan input mapping |
| Audio bermasalah | Uji audio backend terpisah |
| Game tidak bisa boot | Periksa prefix, registry, product code dan runtime |
| Build Docker gagal | Pin dependencies dan simpan build logs |
| Firmware berbeda | Dokumentasikan firmware target dan kompatibilitas |

---

# 11. SCOPE LIMITATIONS

## In Scope

- Menjalankan game PC asli milik pengguna melalui `soccer13`.
- Wine compatibility.
- DXVK integration.
- PS4 runtime integration.
- Native PS4 launcher `SOCCER13`.
- Docker build.
- PKG packaging (`SOCCER13-PS4.pkg`).
- Controller mapping.
- Save data management.

## Out of Scope

- Membuat ulang game dari nol.
- Mengembangkan emulator Xbox 360.
- Membuat XenonRecomp runtime.
- Membuat game engine sepak bola baru.
- Mengembangkan online multiplayer.
- Membuat atau mendistribusikan game assets.
- Menghilangkan copy protection.
- Menyertakan executable game dalam repository.

---

# 12. REFERENCES

Primary repositories:

1. `orbis-win`: https://github.com/plastikman/orbis-win
2. `FUTBOL13`: https://github.com/7tg/futbol13
3. `prospero-win`: https://github.com/plastikman/prospero-win
4. OpenOrbis Toolchain: https://github.com/OpenOrbis/OpenOrbis-PS4-Toolchain

Important documentation:

- `orbis-win` `BUILDING.md`
- `orbis-win` `HARDWARE-STATUS.md`
- `orbis-win` `AGENTS.md`
- `FUTBOL13` `README.md`

`FUTBOL13` harus dijadikan referensi untuk penamaan netral bebas merek dagang, game profile, instalasi game, Wine prefix, konfigurasi `settings.dat`, dan launcher workflow.

`orbis-win` harus menjadi fondasi runtime PS4.

---

# 13. AI CODING AGENT INSTRUCTIONS

AI coding agent harus mengikuti aturan berikut:

1. Jangan langsung menulis seluruh implementasi sebelum melakukan repository audit.
2. Pelajari `orbis-win` secara menyeluruh.
3. Baca `AGENTS.md` dan dokumentasi build sebelum mengubah kode.
4. Gunakan upstream `orbis-win` sebagai fondasi.
5. Jangan mengganti Wine, Mesa, RADV, atau DXVK tanpa alasan teknis yang terukur.
6. Jangan mengasumsikan fitur PS5 dapat digunakan pada PS4.
7. Jangan membuat implementasi API yang belum tersedia.
8. Jangan mengarang dependency, command, atau library.
9. Semua dependency harus dipin.
10. Semua proses build harus melalui Docker.
11. Jangan memasukkan file game atau merek dagang pihak ketiga ke repository.
12. Jangan memasukkan file game ke Docker image.
13. Jangan menghapus konfigurasi atau patch upstream yang sudah terbukti bekerja.
14. Lakukan perubahan kecil dan terukur.
15. Setiap milestone harus menghasilkan deliverable yang dapat diuji.
16. Jalankan host tests sebelum menghasilkan package.
17. Jangan menyatakan game berhasil berjalan tanpa pengujian hardware.
18. Dokumentasikan semua kegagalan dan workaround.

## First Task for AI Agent

Mulai dari Phase 0: Repository Audit.

Jangan langsung mengimplementasikan launcher atau mengubah runtime.

Hasil pertama yang harus dibuat:

- `docs/REPOSITORY-AUDIT.md`
- `docs/DEPENDENCY-MATRIX.md`
- `docs/PS4-COMPATIBILITY-ANALYSIS.md`
- `docs/DOCKER-BUILD-PLAN.md`
- `docs/SOCCER13-COMPATIBILITY-PLAN.md`

Setelah lima dokumen tersebut selesai, berikan laporan feasibility dan daftar blocker sebelum melanjutkan ke implementasi.

---

# 14. DEFINITION OF DONE

Project dinyatakan berhasil apabila:

- Docker dapat membangun seluruh komponen yang diperlukan.
- Native PS4 PKG (`SOCCER13-PS4.pkg`) berhasil dihasilkan.
- PKG dapat diinstal pada PS4 HEN target.
- Wine runtime berhasil dijalankan.
- Game PC asli milik pengguna berhasil dijalankan melalui `SOCCER13`.
- Game mencapai gameplay.
- Controller DualShock 4 berfungsi.
- Audio berfungsi.
- Save data dapat digunakan.
- Game dapat keluar dengan normal.
- Build dan runtime memiliki dokumentasi yang dapat direproduksi.

**Final Objective:**

Menjalankan game sepak bola PC 2013 asli milik pengguna di PS4 HEN sebagai aplikasi homebrew **`SOCCER13`** melalui `orbis-win`, menggunakan Wine + DXVK + Mesa/RADV, dengan build pipeline Docker yang reproducible dan native PS4 homebrew launcher.
