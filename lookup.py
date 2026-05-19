#!/usr/bin/env python3
"""
Look up reference IDs needed before inserting a transaction.

Usage:
  python lookup.py books
  python lookup.py categories
  python lookup.py categories infaq
  python lookup.py partners
  python lookup.py partners melinda
  python lookup.py bank-accounts
"""

import argparse
import sys
from _auth import get_config, get_token, authed_get, login


def books(base_url, token):
    data = authed_get(base_url, token, "/api/books")
    print("\nBuku Kas / Program:")
    for b in data:
        print(f"  id={b['id']}  {b['name']}")
    print()


def categories(base_url, token, query=""):
    data = authed_get(base_url, token, "/api/categories")
    if query:
        data = [c for c in data if query.lower() in c["name"].lower()]
    print("\nKategori:")
    for c in data:
        print(f"  id={c['id']}  {c['name']}")
    print()


def partners(base_url, token, query=""):
    data = authed_get(base_url, token, "/api/partners", params={"query": query} if query else {})
    print("\nWarga (Partner):")
    for p in data:
        phone = f"  {p['phone']}" if p.get("phone") else ""
        print(f"  id={p['id']}  {p['name']}{phone}")
    print()


def bank_accounts(base_url, token):
    data = authed_get(base_url, token, "/api/bank_accounts")
    print("\nRekening (Bank Account):")
    for a in data:
        print(f"  id={a['id']}  {a['name']}  {a.get('account_name', '')}")
    print()


def main():
    parser = argparse.ArgumentParser(description="Look up reference IDs for Buku Masjid")
    parser.add_argument("resource", choices=["books", "categories", "partners", "bank-accounts"])
    parser.add_argument("query", nargs="?", default="", help="Search term (for categories and partners)")
    parser.add_argument("--relogin", action="store_true", help="Force fresh login")
    args = parser.parse_args()

    base_url, email, password, _ = get_config()
    token = get_token(base_url, email, password, args.relogin)

    fn_map = {
        "books": lambda: books(base_url, token),
        "categories": lambda: categories(base_url, token, args.query),
        "partners": lambda: partners(base_url, token, args.query),
        "bank-accounts": lambda: bank_accounts(base_url, token),
    }

    result = fn_map[args.resource]()

    # retry once on token expiry
    if result is None:
        token = login(base_url, email, password)
        fn_map[args.resource]()


if __name__ == "__main__":
    main()
