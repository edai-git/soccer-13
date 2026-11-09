# Phase 0 Deliverable 1: Repository Audit (`docs/REPOSITORY-AUDIT.md`)

**Project:** `soccer13` (SOCCER13 PC → PS4 HEN)  
**Audited Repositories:**
- **Base PS4 Runtime:** [`plastikman/orbis-win`](https://github.com/plastikman/orbis-win) at commit `9d762029157acc94686b2ac76d48ac383938a4fb` (`v0.0.3` / package `01.49`–`01.52`, ABI-v4)
- **Reference Implementation (PS5):** [`7tg/futbol13`](https://github.com/7tg/futbol13) at commit `12294b11f1a97b043e5d2eef82fd8fedeb5bd278`

---

## 1. Executive Summary

Audit terhadap [`plastikman/orbis-win`](https://github.com/plastikman/orbis-win) dan [`7tg/futbol13`](https://github.com/7tg/futbol13) menunjukkan bahwa fondasi teknis untuk menjalankan game sepak bola PC 2013 (32-bit PE32, Direct3D 9, XInput, DirectSound) sebagai aplikasi homebrew **`SOCCER13`** di PS4 HEN **sudah tersedia dan matang** pada generasi **ABI-v4 (`v0.0.3`)**, namun terdapat perbedaan arsitektural mendasar antara cara kerja `orbis-win` (PS4) dan `futbol13` (PS5) yang wajib diperhitungkan sejak awal.

---

## 2. Arsitektur Aktual `plastikman/orbis-win` (PS4)

### 2.1 Struktur Repositori `orbis-win`
- `src/native/`: Layer platform spesifik PS4 (`pw_videoout_ps4.c`, `pw_pad_ps4.c`, `pw_audio_ps4.c`, `pw_platform_bind_ps4.c`, `pw_wow_log_ps4.c`, `pw_osk_ps4.c`, `pw_netctl_ps4.c`, `pw_vulkan_radv_ps4.c`, `pw_prx_env_ps4.c`, `pw_prx_heap_wrap_ps4.c`).
- `src/reloc-wine-app/`: Implementasi **Relocatable Wine Package** khusus PS4 (`stub.c`, `app_entry.c`, `stub-no-relro.ld`).
  - **Mengapa penting untuk `soccer13`:** Kernel Orbis OS memuat PIE `eboot.bin` biasa pada alamat `0x400000`, yang bertabrakan langsung dengan base address executable Windows 32-bit (PE32) non-relocatable (`STATUS_CONFLICTING_ADDRESSES` / `0xc0000018`). `orbis-win` mengatasinya menggunakan `eboot.bin` stub kecil (~56 KB, `no-RELRO` pada `0x55c000`) yang memuat seluruh aplikasi Wine sebagai PRX di alamat tinggi (`/app0/sce_module/relocated_wine_app.prx`), lalu membebaskan ruang alamat rendah sebelum proses Windows 32-bit dijalankan.
- `src/openorbis-module-stubs/`: Source GPL-3.0 dari OpenOrbis untuk membangun `libc.prx` dan `libSceFios2.prx` secara mandiri tanpa memerlukan file modul proprietary dari konsol.
- `src/mesa-patches-ps4/`: Seri patch `0001`–`0044` di atas `orbis-ports/mesa-ps4` (`1a59cc1`), termasuk perbaikan kebocoran memori GPU per-frame (`0041`–`0042`) dan penonaktifan hung-submit dump (`0043`–`0044`) yang sebelumnya menyebabkan stutter/crash.
- `src/wine-patches-ps4/`: Arsip patch Wine khusus PS4 (yang pada generasi ABI-v4 telah diintegrasikan secara reproducible ke dalam seri patch fork [`plastikman/prospero-win`](https://github.com/plastikman/prospero-win) hingga patch `1075`).
- `src/profiles/`: Profil game yang telah teruji di hardware PS4 (GTA IV, Fallout: New Vegas, Fallout 3, Oblivion, Half-Life 2, Half-Life, Titan Quest, Vampire Bloodlines, MDK, Space Cadet Pinball).

### 2.2 Path Runtime di Konsol PS4
Walaupun berjalan di PS4 (Orbis OS), `orbis-win` **tetap menggunakan path `/data/prospero-win/`** di filesystem internal PS4 agar kompatibel dengan library upstream `prospero-win`:
- `/data/prospero-win/profiles/<id>.profile` — Profil konfigurasi game
- `/data/prospero-win/input/<name>.input` — Preset pemetaan kontroler
- `/data/prospero-win/prefixes/<id>/` — Wine prefix lengkap (dibuat di PC dengan Wine yang sama)
- `/data/prospero-win/logs/session-0.log .. session-7.log` — Log sesi aplikasi dan game
- `/data/prospero-win/dev.conf` — Konfigurasi opsional streaming log ke PC (`ps5logd.py` port `9300`)

> **Temuan Kritis #1:** Jangan mengubah path `/data/prospero-win/` menjadi `/data/orbis-win/` tanpa memodifikasi `pw_data_mount.c`, karena seluruh runtime `orbis-win` saat ini mencari prefix, profil, dan log di `/data/prospero-win/`. Untuk `soccer13`, profil akan ditempatkan di `/data/prospero-win/profiles/soccer13.profile` dan prefix di `/data/prospero-win/prefixes/soccer13/`.

### 2.3 Alur Build Upstream `orbis-win`
Terdapat dua jalur build yang terdokumentasi di `orbis-win`:
1. **Jalur Pre-MDK (`docs/BUILDING.md`):**
   - Menjalankan `./scripts/prereqs.sh` dan `./scripts/fetch-sdk.sh` (mengunduh bundle `orbis-ports/orbis-porting-kit` tag `orbis-sdk-v1`).
   - Menyiapkan shim compiler `./scripts/prepare-ps4-toolchain.sh`.
   - Membangun Wine (`build_wine_ps5.sh`), PRX Unix (`scripts/prx-ps4.sh`, `freetype-prx-ps4.sh`, `radv-prx-ps4.sh`, `wineps5-prx-ps4.sh`).
   - Membangun paket relocatable dengan `./scripts/build-relocatable-wine-ps4.sh`.
2. **Jalur Produksi ABI-v4 (`scripts/ci/build-abi4-package.sh` & `.github/workflows/build-ps4-package.yml`):**
   - Menggunakan **Clang/LLVM 19.1.7** (dipin ketat karena perbedaan versi minor menghasilkan machine code berbeda pada `wow64native.prx`).
   - Menggunakan fork [`plastikman/prospero-win`](https://github.com/plastikman/prospero-win) (`50f5b26` / `7fd39cf`) yang mem-build Wine `490f6d5dcbb2a5047345b8af88d114bbcaad69a8` (`wine-11.17-54-g490f6d5dcb`).
   - Menggunakan `scripts/build-openorbis-module-stubs.sh` untuk men-generate `libc.prx` dan `libSceFios2.prx` dari source GPL-3.0 (sehingga **tidak membutuhkan** ekstraksi modul proprietary dari PS4!).
   - Menjalankan pemeriksaan paritas (`scripts/check-ps4-package-parity.py`) dan validasi paket (`PkgTool.Core pkg_validate`).

---

## 3. Perbandingan Arsitektur `orbis-win` (PS4) vs `futbol13` (PS5)

| Aspek | `7tg/futbol13` (PS5) | `plastikman/orbis-win` (PS4) | Implikasi untuk `soccer13` (PS4) |
|---|---|---|---|
| **Format Paket** | Folder app `/data/homebrew/PPSA99405/` (ShadowMount+) | `.pkg` instalasi standar GoldHEN (`IV0000-XXXX_00-...pkg`) | `soccer13` wajib menghasilkan file `.pkg` relocatable untuk PS4 HEN. |
| **Arsitektur EBOOT** | `eboot.bin` adalah Launcher UI (`nfs-blackbox-launcher` + `ps5-opengl`); `game.bin` adalah runner `prospero-win` | `eboot.bin` wajib berupa **56 KB no-RELRO relocation stub** yang memuat `sce_module/relocated_wine_app.prx` agar `0x400000` bebas untuk PE32 | Launcher `SOCCER13` tidak boleh menimpa `eboot.bin` dengan binary besar di `0x400000`. UI `SOCCER13` harus terintegrasi di dalam `relocated_wine_app.prx` (atau memperluas launcher bawaan `orbis-win`). |
| **Pembuatan Wine Prefix** | Membuat *bare prefix* 32-bit saat build di Docker (`bare-prefix-futbol13.zip`), dibundel ke dalam app, lalu diekstrak di konsol saat klik *Install* | Secara default meminta pengguna membuat prefix di PC dengan `wineboot` dan mengirimnya via `pw_prefix.py push` | Kita dapat mengadopsi pendekatan terbaik `futbol13`: mem-build **bare prefix `soccer13`** di dalam Docker container saat build, sehingga pengguna PS4 tidak perlu menginstal Linux/Wine di PC hanya untuk membuat prefix! |
| **Konfigurasi `settings.dat`** | Di-generate otomatis oleh launcher dari template 852 byte (`WECF` v2 + CRC16-XMODEM bitwise NOT) | Belum ada generator khusus `soccer13` | Mengadopsi algoritma generator `settings.dat` (852 byte + CRC-16/XMODEM bitwise NOT) milik `futbol13` dengan resolusi default PS4 `1280×720`. |
| **Registry Startup Game** | Launcher menulis `HKLM\Software\Wow6432Node\KONAMI\PES2013` (`installdir`, `version`, `code` dari `code.txt`), CPU keys (`~MHz`), dan `HKCU\Software\Wine\Direct3D` (`VideoMemorySize="2048"`, `renderer="no3d"`) | Dikonfigurasi di PC sebelum push prefix | Wajib menyertakan injeksi registry yang sama pada prefix `soccer13` agar pemeriksaan instalasi dan pemeriksaan VRAM DirectDraw (minimum 128 MB) lulus di PS4. |
| **Versi DXVK** | DXVK `v3.1.1` + patch custom | DXVK `v2.6.2` (teruji stabil pada Half-Life 2 & GTA IV di PS4 RADV) | Gunakan **DXVK `v2.6.2`** terlebih dahulu sesuai baseline `orbis-win` PS4 RADV, ditambah `dxvk.conf` (`d3d9.memoryTrackTest = True`). |

---

## 4. Kesimpulan Audit Repositori

1. **`orbis-win` (ABI-v4 / `v0.0.3`)** telah memiliki dukungan matang untuk game 32-bit Direct3D 9 dengan **Native WoW64** (`wow64native.dll` + `wow64native.prx`), **DXVK 2.6.2**, **XInput DualShock 4**, serta **DirectShow MP3 audio** (patch Wine `1069`).
2. **`orbis-win` sudah menyertakan OpenOrbis module stubs (`libc.prx`, `libSceFios2.prx`) dari kode sumber GPL-3.0**, sehingga proses build Docker tidak terblokir oleh ketiadaan modul firmware konsol proprietary.
3. **`futbol13`** memberikan cetak biru yang sangat presisi untuk kebutuhan spesifik game (`settings.dat` 852-byte + CRC16, injeksi registry `installdir`/`code`/`VideoMemorySize`, `dxvk.conf`, serta *bare prefix* yang dibuat di dalam Docker).

