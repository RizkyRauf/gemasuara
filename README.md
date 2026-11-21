# Gemasuara

Aplikasi manajemen konten untuk memudahkan posting ke beberapa akun TikTok.

## Fitur

- Autentikasi multi-akun TikTok via OAuth
- Manajemen konten per akun (video + caption)
- Status lifecycle: draft → ready → posted/failed
- Posting manual via CLI (mode draft atau direct post)
- Ringkasan konten per akun

## Struktur Command

```bash
python main.py auth                    # Login akun TikTok
python main.py accounts alias <open_id> <alias>
python main.py content add --account <alias> --video <path> --title "..." --caption "..."
python main.py content list
python main.py content ready <content_id>
python main.py content post <content_id>
python main.py content summary
```

## Setup

1. Salin `.env.example` menjadi `.env`
2. Isi `TIKTOK_CLIENT_KEY`, `TIKTOK_CLIENT_SECRET`, dan `TIKTOK_REDIRECT_URI`
3. Jalankan `python main.py auth`

## Catatan Keamanan

- File `.env`, `tokens.json`, dan `accounts.json` bersifat sensitif dan tidak di-commit ke repository.
- Pastikan client secret dan token tetap aman.
