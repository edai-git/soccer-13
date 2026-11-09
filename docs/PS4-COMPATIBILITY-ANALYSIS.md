# Phase 0 Deliverable 3: PS4 Compatibility Analysis (`docs/PS4-COMPATIBILITY-ANALYSIS.md`)

**Project:** `soccer13` (SOCCER13 PC → PS4 HEN)  
**Target Hardware:** PlayStation 4 (Fat / Slim / Pro) running HEN / GoldHEN

---

## 1. Perbandingan Spesifikasi Hardware PS4 vs Kebutuhan Game

Game sepak bola PC tahun 2013 (`pes2013.exe`) dirancang untuk arsitektur x86 32-bit era DirectX 9.0c (Shader Model 3.0). Berikut perbandingan spesifikasi minimum/rekomendasi game dengan perangkat keras PS4:

| Komponen | Rekomendasi Game PC (2013) | PS4 Fat / Slim (Base) | PS4 Pro (Neo) | Analisis Kompatibilitas |
|---|---|---|---|---|
| **CPU** | Intel Core 2 Duo 2.0 GHz | 8-core AMD Jaguar x86-64 @ **1.6 GHz** | 8-core AMD Jaguar x86-64 @ **2.1 GHz** | **Kompatibel via Native WoW64.** Karena CPU PS4 adalah x86-64, kode 32-bit x86 game dapat dieksekusi secara *native* oleh CPU melalui `wow64native.dll` tanpa overhead translasi instruksi (`wowprospero.dll`). Namun single-thread IPC AMD Jaguar @ 1.6 GHz tergolong rendah, sehingga thread kompilasi shader DXVK dan logging Wine perlu dibatasi. |
| **GPU** | DirectX 9.0c, 512 MB VRAM (Pixel Shader 3.0) | AMD GCN 18 CU @ 800 MHz (**1.84 TFLOPS**) | AMD GCN 36 CU @ 911 MHz (**4.20 TFLOPS**) | **Sangat Memadai.** Beban shader Direct3D 9 (SM 3.0) sangat ringan bagi GPU PS4 Base maupun Pro melalui DXVK → Mesa/RADV. |
| **Memori (RAM/VRAM)** | 2 GB System RAM, min. 128 MB VRAM | **8 GB GDDR5 Unified** (~4.5–5.0 GB tersedia untuk aplikasi) | **8 GB GDDR5 + 1 GB DDR3** (~5.5 GB tersedia untuk aplikasi) | **Memadai dengan Manajemen Memori RADV.** Sebagai aplikasi 32-bit (PE32), ruang alamat guest dibatasi hingga 2–4 GB. Pada `orbis-win` v0.0.3 (Mesa patch `0041`–`0042`), RADV membagi memori 1/3 GTT dan 2/3 VRAM dengan ekstensi arena 1 GiB (`ORBIS_ARENA_EXT_MIB=1024`) dan *per-frame range retirement*. |
| **Resolusi Target** | 1280×720 / 1920×1080 | **1280×720 (Default Baseline)**, 1600×900, 1920×1080 | 1280×720, 1600×900, **1920×1080** | Mulai validasi dari **1280×720** di PS4 Fat/Slim untuk memastikan *frame pacing* 60 FPS stabil sebelum menguji 1080p. |

---

## 2. Evaluasi Sub-Sistem Runtime pada PS4 (`orbis-win` ABI-v4)

### 2.1 Eksekusi CPU & Ruang Alamat Memori (Relocation & WoW64)
1. **Masalah Base Address `0x400000` pada PS4:**
   - Berbeda dengan PS5 (`prospero-win`) yang me-link `eboot.bin` pada alamat tinggi menggunakan `ps5-pie-high.ld`, kernel PS4 (Orbis OS) selalu memuat PIE `eboot.bin` pada `0x400000`.
   - Executable PE32 game (`pes2013.exe`) menggunakan base address standar `0x400000`.
   - **Solusi Terverifikasi di `orbis-win`:** Wajib membangun paket menggunakan `scripts/build-relocatable-wine-ps4.sh` yang menghasilkan `eboot.bin` stub `no-RELRO` (~56 KB) dan memuat aplikasi utama sebagai `/app0/sce_module/relocated_wine_app.prx` di alamat tinggi.
2. **Pemilihan Backend CPU (`cpu = native` vs `cpu = translator`):**
   - `orbis-win` menyediakan dua backend untuk PE32:
     - **Native WoW64 (`cpu = native` / `wow64native.dll` + `wow64native.prx`):** Menjalankan kode 32-bit secara langsung di hardware x86-64 PS4. Terbukti sukses menjalankan 9 dari 10 game referensi (GTA IV, Fallout NV/3, Oblivion, Half-Life 1/2, Titan Quest, Bloodlines).
     - **Software Translator (`cpu = translator` / `wowprospero.dll`):** Hanya digunakan jika game gagal pada mode native (mis. MDK).
   - **Rekomendasi untuk `soccer13`:** Gunakan **`cpu = native`** sebagai default utama karena game sepak bola membutuhkan throughput CPU tinggi untuk AI, fisika bola, dan animasi 22 pemain pada 60 FPS.
3. **Proteksi Halaman Memori (`PW_PS4_FORCE_EXEC=0` & `PW_WINESERVER_HEAP_DIRECT=1`):**
   - Pada executable 32-bit lama yang tidak memiliki flag NX-compatible, Orbis OS secara default dapat memindahkan setiap halaman yang meminta izin baca menjadi *executable* keluar dari *direct memory*.
   - Menyetel `PW_PS4_FORCE_EXEC=0` dan `PW_WINESERVER_HEAP_DIRECT=1` (sebagaimana pada profil Fallout di `orbis-win`) mencegah pengurasan *direct memory* PS4.

### 2.2 Grafis: Direct3D 9 → DXVK → Mesa / RADV (`wsi/orbis`)
1. **Dukungan Vulkan & RADV pada PS4:**
   - GPU PS4 Base (GCN Gen 2 / Sea Islands, Bonaire/Liverpool) dan PS4 Pro (GCN Gen 4 / Polaris) didukung oleh driver `orbis-ports/mesa-ps4` + patch `0001`–`0044` yang menghasilkan `libvulkan.prx`.
   - Patch Mesa `0039` (`wsi_orbis` swapchain sizing) dan patch Wine `1054` memungkinkan ukuran permukaan gambar (*swapchain*) menyesuaikan ukuran jendela/resolusi game (`1280×720`, `1600×900`, `1920×1080`) dan melakukan *scan-out* ke output video PS4 (`libSceVideoOut`).
   - Patch Mesa `0041`–`0042` memperbaiki masalah habisnya *GPU address ranges* pada rendering berkelanjutan dengan melakukan *retire* per-frame pada batas `wsi_orbis` present.
2. **Pemeriksaan VRAM DirectDraw saat Startup Game:**
   - Saat inisialisasi, game memeriksa kapasitas VRAM melalui API `DirectDraw` (`ddraw.dll`), bukan Direct3D 9.
   - Karena PS4 tidak menyediakan OpenGL native untuk `wined3d`, `ddraw` akan jatuh ke adapter *no-3D* milik `wined3d` yang hanya melaporkan 128 MB dikurangi ukuran layar—sehingga dianggap kurang dari syarat minimum 128 MB VRAM oleh game.
   - **Mitigasi Wajib:** Setel registry `HKCU\Software\Wine\Direct3D` dengan `"VideoMemorySize" = "2048"` dan `"renderer" = "no3d"`, serta aktifkan `d3d9.memoryTrackTest = True` di `dxvk.conf`.

### 2.3 Audio: DirectSound / XAudio2 / DirectShow MP3
1. **Output Audio Orbis OS:**
   - `orbis-win` mengimplementasikan output audio melalui `src/native/pw_audio_ps4.c` di atas library native `libSceAudioOut` (`wineps5.drv` / `wineps5.prx`).
2. **Dekode Musik MP3 / DirectShow:**
   - Pada `orbis-win` rilis `v0.0.2` (`01.43`, Wine patch `1069`), masalah absennya GStreamer pada `quartz.dll` dan `l3codecx.ax` telah diperbaiki dengan *built-in MPEG audio splitter* (`mpegaudiosplit.c`) dan DMO wrapper (`mp3dmod`). Hal ini memastikan efek suara dan musik yang menggunakan DirectSound/XAudio2 maupun DirectShow dapat diputar tanpa membocorkan *file descriptor*.

### 2.4 Kontroler: DualShock 4 → `libScePad` → XInput
- `src/native/pw_pad_ps4.c` membaca input dari `libScePad` (DualShock 4) dan meneruskannya ke Wine `xinput1_3.dll` / `dinput8.dll`.
- Profil `soccer13.profile` akan menggunakan:
  - `mode = xinput`
  - `dll_overrides = d3d8,d3d9,d3d10core,d3d11,dxgi=n;dinput8=n,b`
  - `mouse = touchpad` dan `touchpad = mouse_left` (agar touchpad DualShock 4 tetap dapat digunakan sebagai mouse jika diperlukan).
  - Kombinasi **Options + Share (Create)** ditangani oleh runtime untuk menutup game secara bersih apabila keluar dari menu dalam game mengalami kendala.

### 2.5 Batasan Filesystem Orbis OS & FTP GoldHEN
1. **Tidak Ada Pembuatan Symlink Nyata di `/data`:**
   - Aplikasi homebrew di PS4 tidak dapat membuat atau mengikuti symlink POSIX biasa untuk drive Wine (`dosdevices/c:` dan `z:`). `orbis-win` menggunakan file tabel `.pw-symlinks` di setiap direktori.
2. **Bug Server FTP GoldHEN terhadap `MLSD` dan `lftp`:**
   - Sebagaimana didokumentasikan di `orbis-win/docs/INSTALLING-GAMES.md`, server FTP GoldHEN (port `2121`) menolak perintah `MLSD` (`501`) dan dapat mengalami *crash* kernel/HEN jika diakses menggunakan klien `lftp`.
   - Oleh karena itu, seluruh transfer FTP dari host wajib menggunakan script Python minimal (`scripts/ftp-put.py`, `scripts/ftp-get.py`, atau `pw_prefix.py push` tanpa `--trust-size`), dan instalasi lokal di konsol melalui **USB (`/mnt/usb0`..`/mnt/usb7`)** atau folder lokal `/data/` sangat direkomendasikan untuk pengguna akhir.

---

## 3. Perbedaan Pengujian PS4 Fat / Slim vs PS4 Pro

| Parameter | PS4 Fat / Slim (CUH-10xx / 11xx / 12xx / 20xx) | PS4 Pro (CUH-70xx / 71xx / 72xx) |
|---|---|---|
| **Frekuensi CPU** | 1.6 GHz | 2.1 GHz (+31% clock speed) |
| **Dampak pada DXVK Shader Compile** | Kompilasi shader bersamaan dapat memicu frame drop sesaat di awal pertandingan. Batasi `dxvk.numCompilerThreads = 2`. | Lebih toleran terhadap `dxvk.numCompilerThreads = 3` atau `4`. |
| **Target Resolusi Awal** | **1280×720 (Wajib diuji pertama kali)** | 1280×720 → 1920×1080 |
| **Aturan Validasi** | **Hasil lulus di PS4 Pro TIDAK boleh diklaim otomatis lulus di PS4 Fat/Slim.** Setiap model wajib memiliki catatan hasil uji tersendiri. |

