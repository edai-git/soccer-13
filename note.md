Langkah selanjutnya adalah **Pengujian Langsung di Hardware Konsol (Live Hardware Testing di PS4 HEN)**, karena sesuai aturan utama (*Golden Rule 17: Hardware Truth Only*), status keberhasilan game baru sah setelah terbukti berjalan di mesin PS4 fisik.

Berikut adalah 3 langkah praktis yang bisa Anda lakukan sekarang:

---

### Langkah 1: Siapkan File Game PC Anda
Apakah Anda sudah memiliki file instalasi game PC di komputer?
Pastikan Anda memiliki:
1. `pes2013.exe`
2. Folder `img/` (berisi file `.img` seperti `dt00_q.img`, `dt01.img`, dst.)
3. *(Opsional)* Folder mod seperti `kitserver13/` atau file save/patch transfer terbaru.

---

### Langkah 2: Konfigurasi Koneksi PS4 (Opsional tapi Memudahkan)
Jika PS4 Anda terhubung ke jaringan WiFi/LAN yang sama dengan PC, Anda bisa membuat file konfigurasi `.env` di folder project agar script `./scripts/deploy-ps4.sh` dapat mengirim file game dan menarik log secara otomatis:

Buat file `.env` (file ini otomatis diabaikan oleh Git):
```ini
PS4_IP=192.168.1.xxx
PS4_FTP_PORT=2121
```
*(Ganti `192.168.1.xxx` dengan IP PS4 Anda yang terlihat di menu GoldHEN).*

---

### Langkah 3: Eksekusi Pemasangan & Uji Coba

#### Pilihan A (Paling Mudah via Flashdisk USB):
1. Salin file **`release/SOCCER13-PS4.pkg`** ke USB (FAT32/exFAT).
2. Di USB yang sama, buat folder **`SOCCER13`** dan salin file game PC Anda ke dalamnya:
   ```text
   USB:/
   ├── SOCCER13-PS4.pkg
   └── SOCCER13/
       ├── pes2013.exe
       ├── img/
       └── kitserver13/ (jika ada mod)
   ```
3. Colok USB ke PS4, instal `.pkg` lewat menu **GoldHEN Package Installer**, lalu buka aplikasi **SOCCER13**.

#### Pilihan B (Via Jaringan/FTP):
1. Instal `SOCCER13-PS4.pkg` ke PS4.
2. Dari terminal PC, jalankan perintah ini untuk mengunggah game langsung ke harddisk PS4:
   ```bash
   ./scripts/deploy-ps4.sh install-soccer13 "D:/path/ke/folder_game_pc"
   ```

---

### Langkah 4: Evaluasi Hasil di PS4 (12-Stage Checklist)
Saat game dijalankan di PS4, perhatikan apakah:
1. UI Launcher muncul di layar TV dan dapat dikendalikan dengan stik DualShock 4.
2. Saat menekan tombol **PLAY SOCCER13** ($\times$), apakah game masuk ke Main Menu dan Exhibition Match.
3. Apakah suara/audio komentator terdengar dan gameplay berjalan lancar (target 60 FPS pada 720p/1080p).

Jika terjadi kendala atau game crash di tahap tertentu, Anda cukup menjalankan:
```bash
./scripts/deploy-ps4.sh fetch-logs
./scripts/deploy-ps4.sh analyze-logs
```
Log akan langsung dianalisis untuk melihat apakah ada *missing DLL*, alokasi memori grafis, atau shader yang perlu disesuaikan di `dxvk.conf`.

---

**Apakah Anda ingin menyiapkan file game PC dan koneksi FTP sekarang, atau ada bagian konfigurasi launcher/game yang ingin disesuaikan terlebih dahulu?**