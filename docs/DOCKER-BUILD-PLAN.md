# Phase 0 Deliverable 4: Docker Build Plan (`docs/DOCKER-BUILD-PLAN.md`)

**Project:** `soccer13` (SOCCER13 PC → PS4 HEN)  
**Target Workflow:** 100% Reproducible Containerized Build wrapping `plastikman/orbis-win`

---

## 1. Tujuan & Filosofi Desain Docker

Sesuai **Section 5 PRD** dan **Golden Rule #10 (`AGENTS.md`)**:
1. Developer **tidak perlu** menginstal Clang 19, MinGW, Meson, Wine, atau OpenOrbis SDK di mesin host.
2. Container Docker **membungkus (*wraps*) pipeline build resmi `orbis-win`** (`scripts/fetch-sdk.sh`, `scripts/prepare-ps4-toolchain.sh`, `scripts/build-openorbis-module-stubs.sh`, `scripts/prx-ps4.sh`, `scripts/radv-prx-ps4.sh`, `scripts/freetype-prx-ps4.sh`, `scripts/wineps5-prx-ps4.sh`, `scripts/build-relocatable-wine-ps4.sh`) serta pembuatan *bare prefix* dari pendekatan `futbol13`.
3. Seluruh dependency dipin menggunakan versi, commit hash, dan SHA-256 digest.
4. Tidak ada file game proprietary atau firmware dump konsol di dalam image Docker.

---

## 2. Arsitektur Multi-Stage `docker/Dockerfile`

Kami merancang `docker/Dockerfile` dengan base image yang dipin menggunakan digest SHA-256 dan snapshot repositori Ubuntu + LLVM 19.1.7:

```text
+-------------------------------------------------------------------+
| Stage 1: base-toolchain                                           |
| FROM ubuntu:24.04@sha256:534baea6a22c03a63003dbc8dbe78fe34bc0d7... |
| - Pin Ubuntu snapshot (20261012T000000Z)                          |
| - Pin LLVM/Clang 19.1.7 (apt.llvm.org noble)                      |
| - Install MinGW-w64 (i686 & x86_64), CMake, Ninja, Meson, Bison,  |
|   Flex, glslang-tools, Python3, X11/FreeType/Vulkan dev headers   |
| - Install isolated OpenSSL 1.1 (libssl.so.1.1 & libcrypto.so.1.1) |
|   under /opt/openssl11/lib for OpenOrbis PkgTool.Core             |
+-------------------------------------------------------------------+
                                 |
                                 v
+-------------------------------------------------------------------+
| Stage 2: sdk-bundle                                               |
| - Download & verify orbis-sdk-v1.tar.gz + sha256                  |
| - Download & verify freetype-2.13.3.tar.xz (05503506...)          |
| - Download & verify dxvk-2.6.2.tar.gz                             |
| - Run bundle offline verify.sh                                    |
+-------------------------------------------------------------------+
                                 |
                                 v
+-------------------------------------------------------------------+
| Stage 3: builder (Entrypoint: scripts/docker-entrypoint.sh)       |
| - Mounts workspace at /workspace                                  |
| - Uses persistent Docker volume (soccer13-build-cache) at /cache  |
|   for Wine host build, Wine PS4 Unix build, and Mesa RADV build   |
| - Outputs final artifacts to /workspace/artifacts & release/      |
+-------------------------------------------------------------------+
```

---

## 3. Penanganan Tantangan Spesifik `orbis-win` di Dalam Docker

Hasil audit pada Phase 0 menemukan 4 karakteristik teknis `orbis-win` yang wajib ditangani oleh konfigurasi Docker kita:

1. **Persyaratan Versi Clang 19.1.7 yang Ketat:**
   - Workflow CI `orbis-win` (`.github/workflows/build-ps4-package.yml`) memeriksa `clang --version | grep -q 'version 19\.1\.7'`.
   - `Dockerfile` akan memasang `clang-19`, `lld-19`, `llvm-19` dari repositori `apt.llvm.org` dan membuat symlink `/usr/local/bin/clang`, `clang++`, `ld.lld`, `llvm-ar`, `llvm-nm`, `llvm-objcopy`, `llvm-ranlib`, `llvm-readelf`, `llvm-strip`.
2. **Kebutuhan `libssl.so.1.1` oleh `PkgTool.Core`:**
   - Binary `sdk/orbis-sdk-v1/sdk/bin/linux/PkgTool.Core` membutuhkan `libssl.so.1.1` dan `DOTNET_SYSTEM_GLOBALIZATION_INVARIANT=1`.
   - Di dalam container Ubuntu 24.04, kita menyediakan `/opt/openssl11/lib` dan menyetel `LD_LIBRARY_PATH=/opt/openssl11/lib` serta `DOTNET_SYSTEM_GLOBALIZATION_INVARIANT=1` secara otomatis di environment container.
3. **Penggunaan OpenOrbis Module Stubs (Bebas File Konsol Proprietary):**
   - Secara default, `build-app-ps4.sh` mencari `libc.prx` dan `libSceFios2.prx` di `sce_module/`.
   - Namun `orbis-win` telah menyediakan `scripts/build-openorbis-module-stubs.sh` yang mengompilasi `libc.prx` dan `libSceFios2.prx` dari source GPL-3.0 di `src/openorbis-module-stubs/`!
   - Dengan menyetel `PW_MODULE_STUBS_DIR=/cache/openorbis-module-stubs`, build di dalam Docker **tidak memerlukan file proprietary dari konsol PS4 sama sekali**. Jika pengguna tetap ingin menyuplai modul eksternal, `docker-compose.yml` menyediakan bind mount opsional.
4. **Strategi Caching Build dengan Persistent Volume (`soccer13-cache`):**
   - Membangun Wine (Host PE + PS4 Unix) dan Mesa RADV dari nol memakan waktu ~25–35 menit.
   - Dengan me-mount named volume `soccer13-cache:/cache`, hasil kompilasi `wine-host`, `wine-ps5`, `mesa-ps4`, dan `orbis-sdk-v1` disimpan secara persisten di antara eksekusi `docker compose run --rm builder build`, sehingga rebuild incremental launcher/profil `soccer13` hanya membutuhkan waktu beberapa detik.

---

## 4. Kontrak Antarmuka CLI Docker (`docker-compose.yml` & `scripts/`)

Seluruh perintah yang disyaratkan pada **Section 5.4 PRD** dipetakan ke script di `scripts/`:

| Perintah CLI | Script yang Dijalankan | Deskripsi Tugas |
|---|---|---|
| `docker compose build` | Build `docker/Dockerfile` | Membangun image `soccer13-builder` dengan seluruh dependency & SDK yang telah diverifikasi checksum-nya. |
| `docker compose run --rm builder build` | `scripts/build.sh` | Menyiapkan toolchain `orbis-win`, mem-build module stubs, PRX runtime, generator `settings.dat`, profil `soccer13.profile`, *bare prefix*, launcher `SOCCER13`, dan men-stage paket. |
| `docker compose run --rm builder test` | `scripts/test.sh` | Menjalankan seluruh *Host Tests* di dalam Docker: unit test C/C++ launcher, test generator/parser `settings.dat` (CRC-16), validasi `soccer13.profile`, dan audit kebersihan paket/lisensi. |
| `docker compose run --rm builder release` | `scripts/release.sh` | Menjalankan `build` + `test` + `scripts/package.sh` + `scripts/validate.sh` (`PkgTool.Core pkg_validate`), lalu menghasilkan `release/SOCCER13-PS4.pkg`, `BUILD-MANIFEST.txt`, `SHA256SUMS`, dan `THIRD_PARTY.md`. |
| `docker compose run --rm builder clean` | `scripts/build.sh --clean` | Membersihkan direktori build intermediate dan `artifacts/`. |

---

## 5. Struktur Lockfile (`docker/dependencies.lock`)

File `docker/dependencies.lock` akan menyimpan seluruh konstanta versi dan hash yang dibaca oleh `docker/build-env.sh` dan `scripts/validate.sh`:
```ini
UBUNTU_BASE_IMAGE=ubuntu:24.04@sha256:534baea6a22c03a63003dbc8dbe78fe34bc0d7e595d9a9dc9834884ff530eb55
UBUNTU_SNAPSHOT=20261012T000000Z
LLVM_VERSION=19.1.7
ORBIS_WIN_COMMIT=9d762029157acc94686b2ac76d48ac383938a4fb
PROSPERO_WIN_FORK_COMMIT=50f5b26
WINE_COMMIT=490f6d5dcbb2a5047345b8af88d114bbcaad69a8
MESA_PS4_COMMIT=1a59cc1
OPENORBIS_STUBS_COMMIT=0a1aaf9dd4a92695538bdeb09fb056d06dd11725
ORBIS_SDK_TAG=orbis-sdk-v1
DXVK_VERSION=2.6.2
FREETYPE_VERSION=2.13.3
FREETYPE_SHA256=0550350666d427c74daeb85d5ac7bb353acba5f76956395995311a9c6f063289
LLVM_MINGW_VERSION=20260922
LLVM_MINGW_SHA256=bb7bb7654b33d5aa8712acb837c963b2e0c56352560c76105270a3268c665c21
SOURCE_DATE_EPOCH=1767225600
```

