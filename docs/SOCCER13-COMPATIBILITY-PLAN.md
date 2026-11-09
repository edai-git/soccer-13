# Phase 0 Deliverable 5: SOCCER13 Compatibility & Integration Plan (`docs/SOCCER13-COMPATIBILITY-PLAN.md`)

**Project:** `soccer13` (SOCCER13 PC → PS4 HEN)  
**Target Game Binary:** User-supplied 32-bit Windows PE32 (`pes2013.exe` + `img/`)  
**App & Package Identity:** `SOCCER13` (`soccer13.profile`, `SOCCER13-PS4.pkg`)

---

## 1. Karakteristik Teknis Executable & Instalasi (`SOCCER13`)

Berdasarkan audit terhadap implementasi referensi [`7tg/futbol13`](https://github.com/7tg/futbol13) (`profile/pes2013/make-pes2013-plan.py` dan `settings_dat.py`):

1. **Format Binary:** 32-bit Windows Portable Executable (`pe32`), single-process (`pes2013.exe`).
2. **Struktur Direktori Sumber Minimal:**
   - `pes2013.exe` (executable utama)
   - `img/` (berisi arsip data game seperti `dt00_*.img`, `dt05_*.img`, dll.)
   - `code.txt` (file teks 1 baris berisi *product code* instalasi PC milik pengguna, diletakkan di sebelah `pes2013.exe`)
3. **Lokasi di Dalam Wine Prefix (`soccer13`):**
   - Prefix konsol: `/data/prospero-win/prefixes/soccer13/`
   - Direktori game di dalam prefix: `C:\Games\SOCCER13\` (`drive_c/Games/SOCCER13/`)
   - Direktori konfigurasi & save di dalam prefix: `drive_c/users/prospero/Documents/KONAMI/Pro Evolution Soccer 2013/` (path internal yang dibaca secara hardcoded oleh executable game).

---

## 2. Kebutuhan Registry Windows (Startup Checks)

Executable game melakukan tiga pemeriksaan krusial pada Windows Registry saat startup. Jika salah satu gagal, game akan menolak berjalan atau menampilkan pesan error:

### 2.1 Pemeriksaan Instalasi & Product Code (`HKLM`)
Pada prefix 64-bit (`WINEARCH=win64`), aplikasi 32-bit membaca `HKLM\Software\KONAMI\PES2013` yang dipetakan ke **`HKLM\Software\Wow6432Node\KONAMI\PES2013`**:
- `"installdir"` (REG_SZ) = `"C:\\Games\\SOCCER13\\"`  
  *(Game membaca key ini saat startup untuk mencari `img/dt00_*.img` dan `img/dt05_*.img`)*.
- `"version"` (REG_SZ) = `"1.00.0000"`
- `"code"` (REG_SZ) = `<isi dari file code.txt milik pengguna>`  
  *(Tanpa `installdir` atau `code`, game langsung berhenti dengan pesan bahwa game belum terinstal)*.

### 2.2 Pemeriksaan Spesifikasi CPU (`HKLM`)
Karena `wineboot` tidak dijalankan di konsol PS4, prefix harus sudah memiliki informasi prosesor di **`HKLM\Hardware\Description\System\CentralProcessor\0`** (tidak di-redirect ke `Wow6432Node`):
- `"~MHz"` (REG_DWORD) = `1600` (atau `2100` / `3500` agar lulus pemeriksaan frekuensi CPU minimum)
- `"Identifier"` (REG_SZ) = `"AMD64 Family 22 Model 48 Stepping 1"`
- `"VendorIdentifier"` (REG_SZ) = `"AuthenticAMD"`
- `"ProcessorNameString"` (REG_SZ) = `"AMD Jaguar 8-Core Processor"`
- `"FeatureSet"` (REG_DWORD) = `0x1FFF`

### 2.3 Pemeriksaan VRAM via DirectDraw (`HKCU`)
Game memeriksa jumlah VRAM melalui `DirectDraw` (`ddraw.dll` milik Wine `wined3d`), sementara rendering sesungguhnya menggunakan Direct3D 9 (`d3d9.dll` milik DXVK). Agar `ddraw` tidak gagal karena ketiadaan OpenGL atau melaporkan VRAM < 128 MB, wajib menyetel **`HKCU\Software\Wine\Direct3D`**:
- `"VideoMemorySize"` (REG_SZ) = `"2048"`
- `"renderer"` (REG_SZ) = `"no3d"`

---

## 3. Spesifikasi Format Biner `settings.dat` (Tanpa `settings.exe`)

Di PC, `settings.exe` (.NET/WinForms) menulis file biner `settings.dat` berukuran **852 byte (`0x354`)** di folder `Documents\KONAMI\Pro Evolution Soccer 2013\settings.dat`. Di PS4, kita **tidak menjalankan `settings.exe`**, melainkan men-generate `settings.dat` secara langsung menggunakan layout terverifikasi berikut:

| Offset | Tipe | Nilai / Deskripsi |
|---|---|---|
| `0x00` | `char[4]` | Magic header: `"WECF"` (`57 45 43 46`) |
| `0x04` | `uint32_le` | Version: `2` (`02 00 00 00`) |
| `0x08` | `uint32_le` | Payload Size: `0x00000354` (852 byte) |
| `0x0C` | `uint16_le` | **Checksum:** Bitwise NOT (`~crc & 0xFFFF`) dari **CRC-16/XMODEM** (`poly=0x1021`, `init=0x0000`) yang dihitung atas seluruh 852 byte file dengan byte `0x0C` dan `0x0D` diisi `0x00` terlebih dahulu. |
| `0x0E` | `uint16_le` | Flags: `0x00CB` (VSync aktif, Frame Skipping aktif, **XInput aktif**). Nilai `0x00C3` digunakan jika DirectInput. |
| `0x10` | `uint32_le` | **Width** (Resolusi horizontal, mis. `1280` = `0x00000500`, `1600` = `0x00000640`, `1920` = `0x00000780`) |
| `0x14` | `uint32_le` | **Height** (Resolusi vertikal, mis. `720` = `0x000002D0`, `900` = `0x00000384`, `1080` = `0x00000438`) |
| `0x18` | `uint32_le` | Aspect Ratio: `1` (`16:9`) |
| `0x1C` | `uint32_le` | Graphics Quality: `0` = Low, `1` = **Medium** (baseline pengujian PS4), `2` = High |
| `0x20` | `uint32_le` | Display Mode: `1` = Fullscreen, `0` = Windowed |
| `0x28` | `uint32_le` | Network Port: `0x166B` (`5739`) |
| `0x124` | `5 × 0x70 B` | Lima blok konfigurasi perangkat input (keyboard & XInput/DirectInput pad mappings). |

### Algoritma Checksum `settings.dat` (Terverifikasi)
```python
def crc16_xmodem_not(data: bytes) -> int:
    # Byte pada offset 0x0C dan 0x0D harus bernilai 0 sebelum dipanggil
    c = 0
    for b in data:
        c ^= b << 8
        for _ in range(8):
            c = ((c << 1) ^ 0x1021) & 0xFFFF if (c & 0x8000) else (c << 1) & 0xFFFF
    return (~c) & 0xFFFF
```
Unit test di `tests/config/` akan memverifikasi bahwa fungsi generator `settings.dat` menghasilkan checksum yang persis sama dengan vektor uji `settings.exe` (`0x3B3C` untuk 1920×1080 High XInput dan `0x3D6E` untuk 1280×720 High DirectInput).

---

## 4. Konfigurasi DXVK (`app/config/dxvk.conf`)

Untuk memastikan kompatibilitas Direct3D 9 di atas RADV PS4 dan menghindari *stutter* kompilasi shader pada CPU AMD Jaguar:

```ini
# SOCCER13 DXVK configuration for PS4 (orbis-win RADV)
d3d9.maxFrameLatency = 1
d3d9.presentInterval = 1
d3d9.memoryTrackTest = True
dxvk.numCompilerThreads = 2
```
- `d3d9.memoryTrackTest = True` wajib diaktifkan agar pengujian alokasi memori D3D9 oleh game tidak gagal.
- `dxvk.numCompilerThreads = 2` disesuaikan untuk CPU 8-core AMD Jaguar PS4 agar thread kompilasi pipeline Vulkan tidak membuat thread utama game dan audio kelaparan (*thread starvation*).

---

## 5. Rancangan Profil Runtime (`app/profiles/soccer13.profile`)

Berdasarkan format profil `orbis-win` (`docs/INSTALLING-GAMES.md` & `src/profiles/half-life-2.profile` / `gtaiv-test.profile`):

```ini
; SOCCER13 profile for orbis-win (PS4 HEN)
; 32-bit Direct3D 9 via DXVK 2.6.2 on Native WoW64

[application]
id = soccer13
name = SOCCER13
executable = C:\Games\SOCCER13\pes2013.exe
working_directory = C:\Games\SOCCER13
dll_overrides = d3d8,d3d9,d3d10core,d3d11,dxgi=n;dinput8=n,b
prefix = soccer13
runtime = wine-wow64
architecture = pe32
graphics = dxvk

[display]
desktop = 1280x720

[input]
mode = xinput
options = escape
mouse = touchpad
mouse_speed = 400
touchpad = mouse_left

[runtime]
cpu = native

[debug]
env = PW_WINESERVER_HEAP_DIRECT=1;PW_PS4_FORCE_EXEC=0
```

---

## 6. Alur Manajemen Save Data & Proteksi Repair

1. **Lokasi Save di Prefix:**
   `/data/prospero-win/prefixes/soccer13/drive_c/users/prospero/Documents/KONAMI/Pro Evolution Soccer 2013/save/`
2. **File yang Dilindungi:**
   - `EDIT.bin` (data transfer pemain, formasi, skuad/patch)
   - `OPTION.bin` / `SYSTEM` (pengaturan profil dalam game)
   - `ML01.bin` .. `MLxx.bin` / `BL01.bin` (save Master League & Become a Legend)
3. **Aturan Non-Destructive Install & Repair:**
   - Saat pengguna menekan **Install** atau **Repair** di launcher `SOCCER13`, installer menyalin/memperbaiki struktur prefix, `dxvk.conf`, `settings.dat`, dan registry, tetapi **hanya menyalin file ke folder `save/` apabila file tersebut belum ada di dalam prefix**. File save yang sudah ada di konsol tidak pernah ditimpa atau dihapus.

