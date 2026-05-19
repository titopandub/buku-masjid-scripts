#!/usr/bin/env python3
"""
List transactions from Buku Masjid with optional date range filter.

Usage:
  python list_transactions.py
  python list_transactions.py --days 14
  python list_transactions.py --start 2026-05-01 --end 2026-05-17
  python list_transactions.py --days 7 --type pemasukan
"""

import argparse
import sys
from datetime import date, timedelta

from _auth import get_config, get_token, authed_get, login


def format_amount(amount, in_out):
    sign = "+" if in_out == 1 else "-"
    return f"{sign} {amount:>12,.0f}".replace(",", ".")


def main():
    parser = argparse.ArgumentParser(description="List transactions from Buku Masjid")
    parser.add_argument("--days", type=int, default=14, help="Last N days (default: 14)")
    parser.add_argument("--start", help="Start date YYYY-MM-DD (overrides --days)")
    parser.add_argument("--end", help="End date YYYY-MM-DD (default: today)")
    parser.add_argument("--type", choices=["pemasukan", "pengeluaran"], help="Filter by type")
    parser.add_argument("--relogin", action="store_true", help="Force fresh login")
    args = parser.parse_args()

    end_date = date.fromisoformat(args.end) if args.end else date.today()
    start_date = date.fromisoformat(args.start) if args.start else end_date - timedelta(days=args.days - 1)

    base_url, email, password, _ = get_config()
    token = get_token(base_url, email, password, args.relogin)

    params = {
        "start_date": str(start_date),
        "end_date": str(end_date),
    }

    data = authed_get(base_url, token, "/api/transactions", params=params)
    if data is None:
        token = login(base_url, email, password)
        data = authed_get(base_url, token, "/api/transactions", params=params)

    txns = data.get("data", []) if isinstance(data, dict) else data
    txns = [t for t in txns if str(start_date) <= t["date"] <= str(end_date)]

    if args.type:
        in_out_filter = 1 if args.type == "pemasukan" else 0
        txns = [t for t in txns if t.get("in_out") == in_out_filter]

    if not txns:
        print(f"\nTidak ada transaksi dari {start_date} s/d {end_date}.\n")
        return

    print(f"\nTransaksi: {start_date} s/d {end_date}  ({len(txns)} entri)\n")
    print(f"{'ID':>5}  {'Tanggal':<12}  {'Jumlah':>16}  {'Keterangan':<35}  {'Warga':<15}  {'Kategori'}")
    print("-" * 110)

    total_in = 0
    total_out = 0
    for t in txns:
        amount = t.get("amount", 0)
        in_out = t.get("in_out", 1)
        if in_out == 1:
            total_in += amount
        else:
            total_out += amount

        print(
            f"{t['id']:>5}  "
            f"{t['date']:<12}  "
            f"{format_amount(amount, in_out):>16}  "
            f"{(t.get('description') or '')[:35]:<35}  "
            f"{(t.get('partner') or '-')[:15]:<15}  "
            f"{t.get('category') or '-'}"
        )

    print("-" * 110)
    print(f"{'':>5}  {'':12}  {format_amount(total_in, 1):>16}  {'Total Pemasukan'}")
    print(f"{'':>5}  {'':12}  {format_amount(total_out, 0):>16}  {'Total Pengeluaran'}")
    net = total_in - total_out
    sign = "+" if net >= 0 else "-"
    print(f"{'':>5}  {'':12}  {sign} {abs(net):>12,.0f}  {'Saldo Bersih'}".replace(",", "."))
    print()


if __name__ == "__main__":
    main()
