# SOCCER13 (`soccer13`) — PC → PS4 HEN Compatibility Port

![Status](https://img.shields.io/badge/status-initial_specification-blue)
![Target](https://img.shields.io/badge/target-PS4_HEN-003791)
![Build](https://img.shields.io/badge/build-Docker_Reproducible-2496ED)
![Language](https://img.shields.io/badge/language-C%20%2F%20C%2B%2B-00599C)

**SOCCER13** (`soccer13`) adalah aplikasi homebrew dan port kompatibilitas untuk menjalankan salinan pribadi game sepak bola klasik tahun 2013 versi Windows PC secara langsung di **PlayStation 4 (PS4 HEN)** menggunakan pendekatan *compatibility layer* berbasis [`plastikman/orbis-win`](https://github.com/plastikman/orbis-win) dan mengadaptasi pendekatan dari [`7tg/futbol13`](https://github.com/7tg/futbol13).

> **Prinsip Utama:**  
> *"Do not rebuild the game. Run the original Windows game through a PS4-compatible runtime."*  
> Project **`soccer13`** tidak membuat ulang kode sumber, gameplay, fisika, maupun menyertakan aset berhak cipta. Aplikasi ini menjalankan executable dan aset asli milik pengguna di atas runtime kompatibilitas PS4 dengan antarmuka **Native PS4 Homebrew Launcher (`SOCCER13`)**.

---

## Daftar Isi

1. [Gambaran Umum & Tujuan](#1-gambaran-umum--tujuan)
2. [Arsitektur Teknis](#2-arsitektur-teknis)
3. [Fitur Utama](#3-fitur-utama)
4. [Struktur Proyek](#4-struktur-proyek)
5. [Sistem Build (Docker)](#5-sistem-build-docker)
6. [Instalasi & Penggunaan pada PS4](#6-instalasi--penggunaan-pada-ps4)
7. [Pemetaan Kontroler (DualShock 4)](#7-pemetaan-kontroler-dualshock-4)
8. [Tahapan Pengembangan (Roadmap)](#8-tahapan-pengembangan-roadmap)
9. [Strategi Pengujian](#9-strategi-pengujian)
10. [Batasan Ruang Lingkup & Legalitas](#10-batasan-ruang-lingkup--legalitas)
11. [Referensi](#11-referensi)

---

## 1. Gambaran Umum & Tujuan

Project **SOCCER13** (`soccer13`) bertujuan menghasilkan aplikasi homebrew PS4 dalam format `.pkg` (`SOCCER13-PS4.pkg`) yang mampu:

1. Menjalankan executable Windows PC asli (`pes2013.exe` PE32) milik pengguna tanpa memodifikasi folder instalasi sumber.
2. Membaca folder instalasi game PC pengguna yang disalin melalui **USB** atau **FTP**.
3. Menerjemahkan panggilan Win32 API menggunakan **Wine** yang telah diadaptasi untuk Orbis OS melalui **`orbis-win`**.
4. Menerjemahkan rendering **Direct3D 9 ke Vulkan** melalui **DXVK** di atas driver **Mesa / RADV** untuk GPU AMD PS4.
5. Menyediakan dukungan penuh untuk kontroler **DualShock 4** (baik di dalam menu launcher maupun saat gameplay melalui XInput).
6. Mengelola konfigurasi game (`settings.dat`), Wine prefix (`soccer13`), serta backup/restore save data tanpa perlu menjalankan `settings.exe` di konsol.
7. Menyediakan proses build yang **100% reproducible menggunakan Docker**.

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
            SOCCER13 GAMEPLAY
```

### Komponen Utama

| Komponen | Peran & Tanggung Jawab |
|---|---|
| **`orbis-win` Runtime** | Fondasi kompatibilitas Windows pada Orbis OS: integrasi Wine, manajemen memori, eksekusi CPU, audio runtime, dan jembatan ke sistem native PS4. |
| **Wine** | Menjalankan executable Windows PE32, menyediakan Win32 API, Windows registry, virtualisasi filesystem, XInput/DirectInput, dan DirectSound/XAudio. |
| **DXVK** | Menerjemahkan panggilan grafis Direct3D 9 menjadi Vulkan (shader translation, manajemen tekstur, render state, dan sinkronisasi frame). |
| **Mesa / RADV** | Backend driver grafis Vulkan untuk arsitektur GPU AMD GCN pada PS4, menangani alokasi memori GPU, command submission, dan display presentation. |
| **Native Launcher (`SOCCER13`)** | Aplikasi antarmuka native PS4 yang dioperasikan dengan DualShock 4 untuk validasi instalasi, manajemen Wine prefix `soccer13`, pengaturan resolusi/grafis (`settings.dat`), peluncuran game, dan pencatatan log. |

---

## 3. Fitur Utama

- **Manajemen Instalasi Non-Destruktif (FR-01):** Memvalidasi struktur instalasi game PC (executable utama, folder `img/`, ukuran instalasi) dari USB atau FTP dan menyalinnya ke Wine prefix `soccer13` tanpa mengubah file sumber pengguna.
- **Manajemen & Repair Wine Prefix (FR-02):** Mendukung profil Wine prefix khusus `soccer13` (`soccer13.profile`) dengan fitur validasi dan *Repair* yang aman (tidak menghapus save game pengguna).
- **Konfigurasi Otomatis Tanpa `settings.exe` (FR-03 & FR-07):** Mengatur resolusi (`1280×720` default, `1600×900`, `1920×1080`), kualitas grafis, VSync, audio, dan XInput secara langsung melalui pembuatan/pembaruan file `settings.dat`.
- **Manajemen Save Data (FR-08):** Mendukung impor save dari PC, backup, dan restore untuk file `EDIT`, *Option File*, serta *Master League* di dalam folder `save/` pada prefix Wine.
- **Antarmuka Berorientasi Kontroler (Section 4):** Menu utama native PS4 **`SOCCER13`** (`PLAY`, `SETTINGS`, `REPAIR`, `ABOUT`) dengan karya seni bebas hak cipta yang sepenuhnya dinavigasi menggunakan DualShock 4 tanpa memerlukan keyboard atau mouse.
- **Diagnostik & Logging Lengkap (FR-09):** Mencatat log setiap tahap mulai dari inisialisasi launcher, validasi prefix, startup Wine, inisialisasi grafis/audio/kontroler, hingga game exit/crash yang dapat diekspor melalui USB atau FTP.

---

## 4. Struktur Proyek

```text
soccer13/
├── docker/
│   ├── Dockerfile              # Definisi container build dengan dependency yang dipin
│   ├── docker-compose.yml      # Konfigurasi service builder & volume cache
│   ├── build-env.sh            # Script inisialisasi environment & verifikasi checksum
│   └── dependencies.lock       # Lockfile versi SDK, commit submodule, & SHA-256
├── runtime/
│   └── orbis-win/              # Referensi / submodule upstream plastikman/orbis-win
├── app/
│   ├── launcher/               # Source code Native PS4 Homebrew Launcher SOCCER13 (C/C++)
│   │   ├── src/
│   │   ├── include/
│   │   └── CMakeLists.txt
│   ├── profiles/
│   │   └── soccer13.profile    # Konfigurasi environment & runtime untuk SOCCER13
│   └── config/
│       ├── dxvk.conf           # Konfigurasi DXVK untuk PS4 RADV
│       └── settings-template/  # Template settings.dat & registry Windows
├── scripts/
│   ├── build.sh                # Script utama kompilasi seluruh komponen
│   ├── test.sh                 # Eksekusi unit test & validasi di host
│   ├── release.sh              # Pipeline pembuatan paket rilis lengkap
│   ├── package.sh              # Pembuatan file PS4 .pkg (SOCCER13-PS4.pkg)
│   └── validate.sh             # Validasi artefak, lisensi, kebersihan merek dagang, & SHA-256
├── tests/
│   ├── launcher/               # Unit test logika launcher
│   ├── config/                 # Unit test konfigurasi & parser settings.dat
│   ├── package/                # Validasi integritas & kebersihan paket PKG
│   └── integration/            # Pengujian integrasi pipeline build
├── docs/                       # Dokumentasi arsitektur, hasil audit, & panduan
├── artifacts/                  # Direktori output hasil build pada host
├── prd.md                      # Product Requirements Document (Spesifikasi Utama)
├── AGENTS.md                   # Panduan & aturan kerja untuk AI Coding Agent
└── README.md                   # Dokumentasi utama proyek
```

---

## 5. Sistem Build (Docker)

Seluruh proses kompilasi (Wine, Mesa/RADV, DXVK, Native Launcher `SOCCER13`, hingga pemaketan PS4 `.pkg`) dijalankan di dalam **Docker** agar konsisten dan *reproducible*. Anda tidak perlu menginstal compiler Clang/LLVM, OpenOrbis SDK, atau dependency build secara manual di mesin host.

### Prasyarat Host
- **OS:** Linux x86-64 atau Windows dengan **WSL2**
- **Tools:** Docker Engine / Docker Desktop, Git, dan Shell (Bash)
- **Storage:** Ruang penyimpanan yang memadai untuk image, cache kompilasi, dan artefak

### Perintah Build Standar

```bash
# 1. Build Docker image beserta toolchain yang dipin
docker compose build

# 2. Kompilasi seluruh komponen project
docker compose run --rm builder build

# 3. Jalankan seluruh pengujian host (unit test, config validation, package check)
docker compose run --rm builder test

# 4. Buat paket rilis final (SOCCER13-PS4.pkg, manifest, dan SHA256SUMS)
docker compose run --rm builder release

# 5. Bersihkan artefak build
docker compose run --rm builder clean
```

> **Catatan Penting Mengenai Modul Konsol:**  
> Repositori dan Docker image ini **tidak** menyertakan firmware dump PS4, modul proprietary konsol, ataupun file game. Apabila proses build memerlukan modul yang hanya dapat diekstrak dari konsol milik pengguna, sediakan melalui *external bind mount* sesuai petunjuk pada `docs/BUILDING.md`.

---

## 6. Instalasi & Penggunaan pada PS4

1. **Instalasi Paket Homebrew:**
   - Salin file hasil build `SOCCER13-PS4.pkg` ke drive USB (format exFAT).
   - Aktifkan **HEN / GoldHEN** pada konsol PS4 Anda.
   - Masuk ke **Debug Settings → Package Installer** dan instal `SOCCER13-PS4.pkg`.
2. **Menyiapkan File Game PC:**
   - Siapkan folder instalasi game PC asli milik Anda yang minimal memiliki struktur berikut:
     ```text
     SOCCER13/
     ├── pes2013.exe
     ├── img/
     ├── settings.exe
     └── (file instalasi pendukung lainnya)
     ```
   - Hubungkan melalui drive USB atau kirimkan melalui FTP ke lokasi yang ditentukan oleh launcher `SOCCER13`.
3. **Menjalankan Game dari Launcher:**
   - Buka aplikasi **SOCCER13** dari Home Screen PS4.
   - Pastikan indikator **GAME STATUS** menampilkan `Game installed`, `Prefix valid`, dan `Runtime ready`.
   - Sesuaikan pengaturan di menu **SETTINGS** bila diperlukan (disarankan memulai dengan resolusi `1280×720`, kualitas `Medium`).
   - Pilih **PLAY** untuk memulai permainan.

---

## 7. Pemetaan Kontroler (DualShock 4)

Seluruh navigasi menu launcher dan gameplay menggunakan kontroler **DualShock 4** dengan profil pemetaan default berbasis XInput berikut:

| Tombol DualShock 4 | Fungsi di SOCCER13 |
|---|---|
| **Left Stick / D-Pad** | Pergerakan Pemain & Navigasi Menu |
| **Cross (✕)** | Umpan Pendek (*Pass*) / Konfirmasi |
| **Circle (○)** | Umpan Lambung (*Cross*) / *Sliding Tackle* |
| **Square (□)** | Tembakan (*Shoot*) / *Teammate Pressure* |
| **Triangle (△)** | Umpan Terobosan (*Through Pass*) / Kiper Maju |
| **L1** | Ganti Pemain (*Player Switch*) |
| **L2** | Kontrol Spesial / Strategi Manual |
| **R1** | Lari Cepat (*Sprint*) |
| **R2** | Kontrol Rapat (*Special Control / Modifier*) |
| **Options** | Jeda Pertandingan (*Pause*) / Menu |

*(Pemetaan tombol dapat disesuaikan melalui profil input pada menu Settings).*

---

## 8. Tahapan Pengembangan (Roadmap)

Pengembangan dilakukan secara bertahap dengan kriteria kelulusan (*acceptance criteria*) yang ketat di setiap fase:

- [ ] **Phase 0 — Repository Audit:** Audit menyeluruh terhadap [`plastikman/orbis-win`](https://github.com/plastikman/orbis-win) dan [`7tg/futbol13`](https://github.com/7tg/futbol13), pemetaan dependency, evaluasi kompatibilitas PS4, dan penyusunan 5 dokumen rencana teknis di `docs/`.
- [ ] **Phase 1 — Docker Build Infrastructure:** Pembuatan `Dockerfile`, `docker-compose.yml`, lockfile dependency dengan verifikasi SHA-256, dan pembungkusan script build upstream `orbis-win`.
- [ ] **Phase 2 — Baseline Runtime:** Kompilasi baseline `orbis-win` menjadi `.pkg`, instalasi di PS4 HEN target, dan verifikasi menggunakan game Windows referensi yang sudah terbukti kompatibel.
- [ ] **Phase 3 — SOCCER13 Integration:** Pembuatan `soccer13.profile`, penyiapan Wine prefix `soccer13`, validator instalasi executable & `img/`, generator `settings.dat`, serta konfigurasi DXVK & XInput.
- [ ] **Phase 4 — Game Compatibility:** Pengujian dan debugging 12 tahap eksekusi di PS4 (mulai dari startup Wine, menu utama, pemuatan pertandingan, gameplay, audio, kontroler, save/load, hingga keluar dengan bersih).
- [ ] **Phase 5 — Launcher Integration:** Pengembangan UI Native PS4 Launcher `SOCCER13` berbasis DualShock 4, fitur *Install/Repair*, pengaturan resolusi, *performance overlay*, dan manajemen backup save data.
- [ ] **Phase 6 — Release:** Pembuatan paket rilis final (`SOCCER13-PS4.pkg`), audit lisensi (`THIRD_PARTY.md`), pembuatan `BUILD-MANIFEST.txt` dan `SHA256SUMS`, serta validasi akhir pada perangkat keras PS4.

> **Untuk Kontributor & AI Coding Agent:** Bacalah **[AGENTS.md](./AGENTS.md)** dan **[prd.md](./prd.md)** sebelum memulai pekerjaan. Pekerjaan **wajib** dimulai dari **Phase 0 (Repository Audit)**.

---

## 9. Strategi Pengujian

Project ini membagi pengujian menjadi dua lapisan:

1. **Host Tests (Di dalam Docker tanpa PS4):**
   - Verifikasi build Docker & integritas checksum dependency
   - Validasi sintaks & skema `soccer13.profile` serta `settings.dat`
   - Unit test logika Native Launcher `SOCCER13`
   - Validasi struktur paket `.pkg`, audit lisensi, dan pemeriksaan bebas file/merek dagang proprietary
2. **PS4 Hardware Tests (Pada Konsol PS4 HEN Target):**
   - Verifikasi berurutan dari instalasi PKG → pembukaan Launcher → inisialisasi Wine → startup game process → Main Menu → Match Loading → Gameplay → Audio → DualShock 4 Input → Save/Load → Exit ke Launcher.
   - Setiap pengujian wajib mencatat model konsol (**PS4 Fat / Slim / Pro**), versi Firmware, versi HEN, versi PKG, ABI runtime, dan lokasi file log.

---

## 10. Batasan Ruang Lingkup & Legalitas

### Di Dalam Ruang Lingkup (*In Scope*)
- Menjalankan salinan pribadi game PC asli milik pengguna melalui Wine + DXVK + Mesa/RADV di atas `orbis-win`.
- Pengembangan Native PS4 Launcher **`SOCCER13`**, pengelolaan Wine prefix, pemetaan DualShock 4, dan manajemen save data.
- Infrastruktur build Docker yang *reproducible* dan pemaketan `.pkg` homebrew (`SOCCER13-PS4.pkg`).

### Di Luar Ruang Lingkup (*Out of Scope*)
- Membuat ulang (*remake*) game atau mengembangkan game engine baru.
- Mengembangkan emulator Xbox 360 / PS3 atau XenonRecomp runtime.
- Fitur *online multiplayer*.
- Membajak, melewati proteksi salinan (*DRM/copy protection bypass*), atau mendistribusikan executable maupun aset game berhak cipta.

### Disclaimer Legal
**SOCCER13** (`soccer13`) adalah proyek kompatibilitas dan *launcher* sumber terbuka independen yang **tidak berafiliasi dengan Konami Digital Entertainment maupun Sony Interactive Entertainment**. Repositori dan paket aplikasi ini **tidak menyertakan kode, executable, logo, merek dagang, aset grafis/audio (`img/`), maupun firmware berhak cipta milik pihak ketiga**. Untuk menggunakan perangkat lunak ini, pengguna wajib memiliki salinan resmi game PC milik sendiri.

---

## 11. Referensi

- **orbis-win (Base PS4 Runtime):** [https://github.com/plastikman/orbis-win](https://github.com/plastikman/orbis-win)
- **FUTBOL13 (PS5 Reference Implementation):** [https://github.com/7tg/futbol13](https://github.com/7tg/futbol13)
- **prospero-win (PS5 Runtime Reference):** [https://github.com/plastikman/prospero-win](https://github.com/plastikman/prospero-win)
- **OpenOrbis PS4 Toolchain:** [https://github.com/OpenOrbis/OpenOrbis-PS4-Toolchain](https://github.com/OpenOrbis/OpenOrbis-PS4-Toolchain)
- **Dokumen Spesifikasi Produk (PRD):** [prd.md](./prd.md)
- **Instruksi AI Coding Agent:** [AGENTS.md](./AGENTS.md)
