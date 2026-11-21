import json
import os
import secrets
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

# File penyimpanan token per akun
TOKENS_FILE = Path(__file__).parent / "tokens.json"


def _load_tokens():
    if TOKENS_FILE.exists():
        return json.loads(TOKENS_FILE.read_text())
    return {}


def _save_tokens(tokens):
    TOKENS_FILE.write_text(json.dumps(tokens, indent=2))


def get_client_credentials():
    """Ambil client_key, client_secret, dan redirect_uri dari environment."""
    client_key = os.getenv("TIKTOK_CLIENT_KEY")
    client_secret = os.getenv("TIKTOK_CLIENT_SECRET")
    redirect_uri = os.getenv("TIKTOK_REDIRECT_URI")

    if not all([client_key, client_secret, redirect_uri]):
        raise ValueError(
            "TIKTOK_CLIENT_KEY, TIKTOK_CLIENT_SECRET, dan TIKTOK_REDIRECT_URI wajib diisi di .env"
        )

    return client_key, client_secret, redirect_uri


def get_auth_url(scopes=None):
    """Buat URL authorisasi TikTok OAuth2."""
    if scopes is None:
        # video.publish = Direct Post
        # user.info.basic = info profil dasar
        scopes = ["video.publish", "user.info.basic"]

    client_key, _, redirect_uri = get_client_credentials()
    state = secrets.token_urlsafe(16)
    scope_str = ",".join(scopes)

    url = (
        "https://www.tiktok.com/v2/auth/authorize/"
        f"?client_key={client_key}"
        f"&response_type=code"
        f"&scope={scope_str}"
        f"&redirect_uri={redirect_uri}"
        f"&state={state}"
    )
    return url, state


def _call_token_endpoint(payload):
    """Helper untuk panggil endpoint TikTok OAuth token."""
    client_key, client_secret, redirect_uri = get_client_credentials()

    payload = dict(payload)
    payload["client_key"] = client_key
    payload["client_secret"] = client_secret

    resp = requests.post(
        "https://open.tiktokapis.com/v2/oauth/token/",
        data=payload,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    resp.raise_for_status()

    data = resp.json()
    error = data.get("error", {})
    if error.get("code") != "ok":
        raise RuntimeError(f"OAuth error: {error}")

    return data["data"]


def exchange_code(code):
    """Tukar authorization code jadi access_token dan refresh_token."""
    _, _, redirect_uri = get_client_credentials()

    token_data = _call_token_endpoint({
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": redirect_uri,
    })

    # Simpan waktu kedaluwarsa agar bisa refresh otomatis nanti
    token_data["expires_at"] = time.time() + token_data.get("expires_in", 7199)

    open_id = token_data.get("open_id")
    if not open_id:
        raise RuntimeError("open_id tidak ditemukan di response token")

    tokens = _load_tokens()
    tokens[open_id] = token_data
    _save_tokens(tokens)

    return token_data


def refresh_token(open_id):
    """Refresh access_token untuk akun tertentu."""
    tokens = _load_tokens()
    if open_id not in tokens:
        raise ValueError(f"Akun {open_id} belum pernah login")

    refresh = tokens[open_id].get("refresh_token")
    if not refresh:
        raise ValueError(f"Tidak ada refresh_token untuk akun {open_id}")

    token_data = _call_token_endpoint({
        "refresh_token": refresh,
        "grant_type": "refresh_token",
    })
    token_data["expires_at"] = time.time() + token_data.get("expires_in", 7199)

    tokens[open_id] = token_data
    _save_tokens(tokens)

    return token_data


def get_valid_access_token(open_id):
    """Ambil access_token yang masih berlaku, refresh jika sudah mau expired."""
    tokens = _load_tokens()
    if open_id not in tokens:
        raise ValueError(f"Akun {open_id} belum pernah login. Jalankan: python main.py auth")

    token = tokens[open_id]
    expires_at = token.get("expires_at", 0)

    # Refresh kalau token expired dalam 5 menit ke depan
    if time.time() >= expires_at - 300:
        token = refresh_token(open_id)

    return token["access_token"]


def list_accounts():
    """Tampilkan semua akun yang sudah login."""
    tokens = _load_tokens()
    result = []
    for open_id, token in tokens.items():
        result.append({
            "open_id": open_id,
            "scope": token.get("scope", ""),
            "expires_at": token.get("expires_at", 0),
        })
    return result
