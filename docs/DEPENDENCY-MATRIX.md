# Phase 0 Deliverable 2: Dependency Matrix (`docs/DEPENDENCY-MATRIX.md`)

**Project:** `soccer13` (SOCCER13 PC → PS4 HEN)  
**Status:** Verified against `plastikman/orbis-win` (`9d762029`) & `7tg/futbol13` (`12294b11`)

---

## 1. Pinned Source Repositories & Commits

Seluruh repositori sumber yang digunakan dalam pipeline build `soccer13` wajib dipin pada commit hash berikut:

| Komponen | Repository URL | Branch / Tag | Commit Hash / Pin | Lisensi | Catatan |
|---|---|---|---|---|---|
| **orbis-win (PS4 Runtime Layer)** | `https://github.com/plastikman/orbis-win.git` | `main` (`v0.0.3+`) | `9d762029157acc94686b2ac76d48ac383938a4fb` | LGPL-2.1-or-later | Submodule di `runtime/orbis-win` |
| **prospero-win (PS4 ABI-v4 Fork)** | `https://github.com/plastikman/prospero-win.git` | `main` | `50f5b26` (atau `7fd39cf` dengan fix quit hang `1074`/`1075`) | LGPL-2.1-or-later | Menyediakan `tools/build_wine_ps5.sh`, `build_host_wine.sh`, dan seri patch Wine ABI-v4 |
| **Wine Upstream Mirror** | `https://github.com/wine-mirror/wine.git` | `wine-11.17-54-g490f6d5dcb` | `490f6d5dcbb2a5047345b8af88d114bbcaad69a8` | LGPL-2.1-or-later | Dipin di dalam `tools/build_wine_ps5.sh` (`WINE_COMMIT`) |
| **Mesa PS4 (RADV + `wsi/orbis`)** | `https://github.com/orbis-ports/mesa-ps4.git` | `main` | `1a59cc1` + `src/mesa-patches-ps4/0001`–`0044` | MIT | Membangun `libvulkan_radeon.a` → `libvulkan.prx` |
| **OpenOrbis Module Stubs** | Tracked in `orbis-win/src/openorbis-module-stubs/` | Upstream `@0a1aaf9` | `0a1aaf9dd4a92695538bdeb09fb056d06dd11725` | GPL-3.0 | Menghasilkan `libc.prx` dan `libSceFios2.prx` tanpa blob Sony |

---

## 2. Prebuilt SDK, Toolchains & Archive Tarballs (With SHA-256)

| Artefak / Bundle | Sumber / URL | Versi / Tag | SHA-256 Checksum / Verifikasi | Kegunaan |
|---|---|---|---|---|
| **Orbis SDK Bundle (`orbis-sdk-v1`)** | `https://github.com/orbis-ports/orbis-porting-kit/releases/download/orbis-sdk-v1/orbis-sdk-v1.tar.gz` | `orbis-sdk-v1` | Diverifikasi via `orbis-sdk-v1.tar.gz.sha256` + offline `verify.sh` (`BUNDLE.txt`) | Menyediakan OpenOrbis SDK (`create-fself`, `create-gp4`, `PkgTool.Core`, `link.x`, `crtlib.o`), `orbis-compat`, dan prebuilt Mesa baseline |
| **DXVK (Baseline PS4)** | `https://github.com/doitsujin/dxvk/releases/download/v2.6.2/dxvk-2.6.2.tar.gz` | `v2.6.2` | Diverifikasi saat unduh (atau dibangun dari source) | Menyediakan DLL 32-bit (`x32/d3d9.dll`, `dxgi.dll`, `d3d8.dll`, `d3d10core.dll`, `d3d11.dll`) yang telah teruji di `orbis-win` (Half-Life 2 & GTA IV) |
| **DXVK (Alternatif Source Build)** | `https://github.com/doitsujin/dxvk.git` | `v3.1.1` | Commit `b1a1c99ab52b687cf950d62c88bc2fa316b41663` | Digunakan oleh `futbol13` bersama patch 32-bit refcount; kandidat cadangan jika DXVK `2.6.2` menemui kendala pada `soccer13` |
| **FreeType Tarball** | `https://download.savannah.gnu.org/releases/freetype/freetype-2.13.3.tar.xz` | `2.13.3` | `0550350666d427c74daeb85d5ac7bb353acba5f76956395995311a9c6f063289` | Dibutuhkan untuk membangun `libfreetype.prx` (`scripts/freetype-prx-ps4.sh`) |
| **llvm-mingw (untuk Mesa Zink jika diperlukan)** | `https://github.com/mstorsjo/llvm-mingw/releases/download/20260922/llvm-mingw-20260922-ucrt-ubuntu-22.04-x86_64.tar.xz` | `20260922` | `bb7bb7654b33d5aa8712acb837c963b2e0c56352560c76105270a3268c665c21` | Cross-compiler PE32/PE64 untuk `build_mesa_zink.sh` |
| **`wow64native.dll` (ABI-v4 PE)** | Dibangun oleh `prospero-win/tools/build_wow64native.sh` | ABI-v4 | `e531a51bb19ae4f92e65556f0f6d4f89e930b9c7490d8a02988feb1d5ee9c044` | Backend CPU WoW64 native untuk eksekusi PE32 di atas x86_64 PS4 |
| **`wow64native.prx` (ABI-v4 PRX)** | Dibangun oleh `scripts/prx-ps4.sh` + `create-fself-repro.sh` | ABI-v4 | `20eee436ae5856f06d39b9f9fa57720806612f15e1ebea4ab15b4638da5b729d` | Modul pendamping Unix PRX untuk `wow64native.dll` |

---

## 3. Container & Host Build Dependencies (Docker)

### 3.1 Base Container Image
- **Image:** `ubuntu:24.04@sha256:534baea6a22c03a63003dbc8dbe78fe34bc0d7e595d9a9dc9834884ff530eb55` (Linux `amd64`)
- **Ubuntu Archive Snapshot:** `20261012T000000Z` (menjamin apt package yang terinstal selalu menghasilkan versi byte-identik).

### 3.2 Toolchain & Apt Packages Wajib
Berdasarkan `.github/workflows/build-ps4-package.yml`, `scripts/prereqs.sh`, dan `docs/INSTALLING-GAMES.md`:
1. **LLVM / Clang Toolchain:**
   - **Versi Wajib:** `clang-19`, `lld-19`, `llvm-19` (**19.1.7** dari `apt.llvm.org/noble/ llvm-toolchain-noble-19`).
   - **Alasan Teknis:** `scripts/ci/build-abi4-package.sh` memverifikasi bahwa `clang --version` adalah `19.1.7` agar output kompilasi `wow64native.prx` cocok dengan pin SHA-256 (`20eee436...`).
2. **MinGW-w64 Cross-Compiler (untuk PE32/PE64 Wine & DXVK):**
   - `gcc-mingw-w64-i686`, `g++-mingw-w64-i686`, `gcc-mingw-w64-x86-64`, `g++-mingw-w64-x86-64`
3. **Build Systems & Generators:**
   - `build-essential`, `cmake`, `ninja-build`, `meson`, `pkg-config`, `bison`, `flex`, `perl`, `gettext`, `python3`, `python3-venv`, `python3-pip`, `python3-yaml`
4. **Shader & Graphics Build Tools:**
   - `glslang-tools` (`glslangValidator`), `spirv-tools`
5. **Host Wine Build Libraries (untuk membangun `wine-host` guna men-generate bare prefix `soccer13`):**
   - `libx11-dev`, `libxext-dev`, `libfreetype-dev`, `libfontconfig-dev`, `libvulkan-dev`, `libgnutls28-dev`, `libasound2-dev`, `libpulse-dev`, `zlib1g-dev`
6. **OpenSSL 1.1 Runtime (`libssl.so.1.1` & `libcrypto.so.1.1`):**
   - **Temuan Penting:** `PkgTool.Core` (binary .NET Core lama di dalam OpenOrbis SDK `sdk/orbis-sdk-v1/sdk/bin/linux/PkgTool.Core`) membutuhkan `libssl.so.1.1` dan `libcrypto.so.1.1` melalui `LD_LIBRARY_PATH` serta `DOTNET_SYSTEM_GLOBALIZATION_INVARIANT=1` saat menjalankan `make-pkg.sh` dan `pkg_validate`. Di Ubuntu 24.04 (yang secara default membawa OpenSSL 3), `libssl1.1` (`1.1.1f` / `1.1.1w` `.deb` dengan SHA-256 yang dipin) wajib dipasang ke direktori khusus (mis. `/opt/openssl11/lib`).

---

## 4. Non-Redistributable & External Inputs

Komponen berikut **dilarang keras** dimasukkan ke dalam repositori Git maupun Docker image:

| Input Eksternal | Disuplai Oleh | Mekanisme Penyediaan | Status di Build Docker |
|---|---|---|---|
| **Instalasi Game PC (`pes2013.exe`, `img/`, dll.)** | Pengguna akhir | USB drive (`/mnt/usb0..7/SOCCER13/` atau `PES2013/`) atau FTP (`/data/soccer13/base-games/`) | **Tidak dibutuhkan** saat build `.pkg` (hanya dibutuhkan saat pengujian di PS4 atau host-install test). |
| **Product Code (`code.txt`)** | Pengguna akhir | File teks 1 baris di dalam folder game pengguna | **Tidak dibutuhkan** saat build `.pkg`. |
| **Save Data Pengguna (`save/`)** | Pengguna akhir | Opsional melalui USB / FTP | **Tidak dibutuhkan** saat build `.pkg`. |
| **Sony `libc.prx` & `libSceFios2.prx` Asli** | Tidak diperlukan untuk CI/Release | Digantikan oleh `scripts/build-openorbis-module-stubs.sh` (OpenOrbis GPL-3.0 stubs) | **Tidak dibutuhkan** (dibangun dari source GPL-3.0). |
| **Konfigurasi IP Konsol (`config.env` / `dev.conf`)** | Developer lokal | File `.env` / `config.env` yang di-gitignore | Opsional, hanya untuk deployment FTP & live logging. |

