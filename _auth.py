"""Shared auth, config, and HTTP helpers for Buku Masjid scripts."""

import json
import os
import sys
from pathlib import Path

_env_file = Path(__file__).parent / ".env.script"
if _env_file.exists():
    for line in _env_file.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())

try:
    import requests
except ImportError:
    sys.exit("Missing dependency: pip install requests")

TOKEN_CACHE = Path(__file__).parent / ".token_cache.json"


def get_config():
    url = os.environ.get("BUKU_MASJID_URL", "").rstrip("/")
    email = os.environ.get("BUKU_MASJID_EMAIL", "")
    password = os.environ.get("BUKU_MASJID_PASSWORD", "")
    book_id = os.environ.get("BUKU_MASJID_BOOK_ID", "")
    if not url or not email or not password:
        sys.exit(
            "Missing config. Set BUKU_MASJID_URL, BUKU_MASJID_EMAIL, "
            "BUKU_MASJID_PASSWORD in .env.script"
        )
    return url, email, password, book_id


def login(base_url: str, email: str, password: str) -> str:
    resp = requests.post(
        f"{base_url}/api/auth/login",
        json={"email": email, "password": password},
        timeout=10,
    )
    if not resp.ok:
        sys.exit(f"Login failed ({resp.status_code}): {resp.text}")
    token = resp.json().get("access_token")
    if not token:
        sys.exit(f"No access_token in login response: {resp.text}")
    TOKEN_CACHE.write_text(json.dumps({"access_token": token}))
    TOKEN_CACHE.chmod(0o600)
    return token


def get_token(base_url: str, email: str, password: str, force: bool = False) -> str:
    if not force and TOKEN_CACHE.exists():
        try:
            data = json.loads(TOKEN_CACHE.read_text())
            if data.get("access_token"):
                return data["access_token"]
        except Exception:
            pass
    return login(base_url, email, password)


def authed_get(base_url: str, token: str, path: str, params: dict = None):
    resp = requests.get(
        f"{base_url}{path}",
        headers={"Authorization": f"Bearer {token}"},
        params=params or {},
        timeout=10,
    )
    if resp.status_code == 401:
        return None  # signal token expired
    if not resp.ok:
        sys.exit(f"GET {path} failed ({resp.status_code}): {resp.text}")
    return resp.json()
