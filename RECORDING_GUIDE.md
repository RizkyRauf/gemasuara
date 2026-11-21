# Panduan Rekam Demo Video App Review

Panduan ini membantu kamu merekam demo video untuk submission App Review TikTok Developer.

## Persyaratan Demo Video

- Format: **MP4** atau **MOV**
- Maksimal: **5 file, 50MB per file**
- Durasi ideal: **1–2 menit**
- Harus menunjukkan **end-to-end flow** integrasi dengan TikTok
- Domain website di video harus sama dengan **Web/Desktop URL** yang didaftarkan

## Alat Rekam Layar

### Linux

```bash
# SimpleScreenRecorder
sudo dnf install simplescreenrecorder

# atau Kazam
sudo dnf install kazam
```

### Windows

- **Xbox Game Bar**: tekan `Win + G`
- **OBS Studio**: https://obsproject.com

### Mac

- Buka **QuickTime Player** → File → New Screen Recording

## Persiapan Sebelum Rekam

1. **Perbesar font terminal** supaya mudah dibaca
   - Di terminal: `Ctrl + Shift + +` beberapa kali

2. **Bersihkan desktop** — tutup aplikasi/tab yang tidak perlu

3. **Pastikan `.env` sudah terisi** dengan benar

4. **Pastikan Redirect URI sudah didaftarkan** di TikTok Developer:
   ```
   https://rizkyrauf.github.io/gemasuara/callback.html
   ```

5. **Siapkan akun TikTok** yang akan digunakan untuk demo

6. **Siapkan aplikasi TikTok di HP** untuk menunjukkan draft masuk

## Flow yang Harus Direkam

### Scene 1 — Landing Page (5–10 detik)

Buka browser dan akses:
```
https://rizkyrauf.github.io/gemasuara/
```

Tunjukkan:
- Nama aplikasi: Gemasuora
- Features
- Privacy Policy dan Terms of Service links

### Scene 2 — Autentikasi TikTok (30–45 detik)

Di terminal, jalankan:
```bash
python main.py auth
```

Tunjukkan:
- URL OAuth muncul di terminal
- Buka URL di browser
- Login ke TikTok
- Klik tombol authorize
- Halaman callback menampilkan authorization code
- Copy code dan paste ke terminal
- Pesan sukses login

### Scene 3 — Manajemen Konten (45–60 detik)

Jalankan command satu per satu:

```bash
python main.py accounts
python main.py accounts alias <open_id> demo-account
python main.py content add --account demo-account --video /tmp/gemasuara_demo_video.mp4 --title "Demo" --caption "Demo post from Gemasuara #gemasuara"
python main.py content list
python main.py content ready <content_id>
python main.py content post <content_id>
```

Tunjukkan:
- Alias akun berhasil dibuat
- Konten berhasil dibuat
- Status berubah dari draft → ready
- Post berhasil dengan publish ID

### Scene 4 — Hasil di Aplikasi TikTok (15–20 detik)

Buka aplikasi TikTok di HP:
- Masuk ke akun yang sama
- Buka notifikasi atau bagian inbox/draft
- Tunjukkan video demo sudah masuk sebagai draft

## Tips Agar Video Berkualitas

1. **Jangan terlalu cepat** — beri jeda antar command
2. **Gunakan kursor mouse** untuk menunjuk bagian penting
3. **Jelaskan dengan suara** atau tambahkan text overlay
4. **Pastikan terminal dan browser terlihat jelas**
5. **Hindari informasi sensitif** seperti client secret atau token lengkap

## Menggunakan Script Demo

Kami sudah menyediakan script demo yang memandu step-by-step:

```bash
./scripts/demo.sh
```

Script ini akan:
- Membuat video demo otomatis
- Menjalankan command satu per satu
- Berhenti di setiap step menunggu kamu tekan ENTER

## Setelah Rekam

1. Cek ukuran file — pastikan di bawah 50MB
2. Cek durasi — ideal 1–2 menit
3. Upload ke field **Demo video** di TikTok Developer Portal
4. Isi explanation text
5. Submit App Review

## Catatan Penting

- **Jangan gunakan video dari internet** — video demo harus menunjukkan aplikasi kamu sendiri
- **Domain di video harus sama** dengan Web/Desktop URL yang didaftarkan
- **Jangan tampilkan client secret** atau access token lengkap di video
