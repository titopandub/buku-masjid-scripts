#!/usr/bin/env python3
"""
Insert a pemasukan (income) or pengeluaran (expense) into Buku Masjid.

Usage:
  python transaction.py pemasukan 500000 "Infaq Jumat"
  python transaction.py pengeluaran 150000 "Beli sabun" --date 2026-05-04
  python transaction.py pemasukan 10000 "Infaq dari Hamba Allah" \
      --date 2026-05-04 --book-id 2 --category-id 5 --partner-id 3 --bank-account-id 1

Run 'python lookup.py <books|categories|partners|bank-accounts>' to find IDs.
"""

import argparse
import json
import sys
from datetime import date

from _auth import get_config, get_token, login

try:
    import requests
except ImportError:
    sys.exit("Missing dependency: pip install requests")


def create_transaction(base_url, token, payload):
    resp = requests.post(
        f"{base_url}/api/transactions",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
        timeout=10,
    )
    if resp.status_code == 401:
        return None  # token expired
    if not resp.ok:
        sys.exit(f"Failed ({resp.status_code}): {resp.text}")
    return resp.json()


def main():
    parser = argparse.ArgumentParser(description="Insert a transaction into Buku Masjid")
    parser.add_argument("type", choices=["pemasukan", "pengeluaran"])
    parser.add_argument("amount", type=int, help="Jumlah dalam Rupiah, e.g. 500000")
    parser.add_argument("description", help="Keterangan transaksi")
    parser.add_argument("--date", default=str(date.today()), help="Tanggal YYYY-MM-DD (default: hari ini)")
    parser.add_argument("--book-id", help="ID Buku Kas (overrides BUKU_MASJID_BOOK_ID)")
    parser.add_argument("--category-id", help="ID Kategori (opsional)")
    parser.add_argument("--partner-id", help="ID Warga (opsional)")
    parser.add_argument("--bank-account-id", help="ID Rekening (opsional)")
    parser.add_argument("--relogin", action="store_true", help="Force fresh login")
    args = parser.parse_args()

    base_url, email, password, default_book_id = get_config()
    token = get_token(base_url, email, password, args.relogin)

    book_id = args.book_id or default_book_id
    if not book_id:
        sys.exit(
            "book_id wajib diisi. Gunakan --book-id atau set BUKU_MASJID_BOOK_ID di .env.script\n"
            "Jalankan: python lookup.py books"
        )

    payload = {
        "date": args.date,
        "amount": str(args.amount),
        "in_out": 1 if args.type == "pemasukan" else 0,
        "description": args.description,
        "book_id": int(book_id),
        "category_id": int(args.category_id) if args.category_id else None,
        "partner_id": int(args.partner_id) if args.partner_id else None,
        "bank_account_id": int(args.bank_account_id) if args.bank_account_id else None,
    }

    result = create_transaction(base_url, token, payload)
    if result is None:
        token = login(base_url, email, password)
        result = create_transaction(base_url, token, payload)
        if result is None:
            sys.exit("Autentikasi gagal setelah re-login.")

    data = result.get("data", {})
    label = "Pemasukan" if payload["in_out"] == 1 else "Pengeluaran"
    print(f"\n✓ {label} berhasil ditambahkan")
    print(f"  ID         : {data.get('id')}")
    print(f"  Tanggal    : {data.get('date')}")
    print(f"  Jumlah     : {data.get('amount_string')}")
    print(f"  Keterangan : {data.get('description')}")
    print(f"  Buku       : {data.get('book')}")
    print(f"  Kategori   : {data.get('category') or '-'}")
    print(f"  Warga      : {data.get('partner') or '-'}")
    print()
    print("JSON:", json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
