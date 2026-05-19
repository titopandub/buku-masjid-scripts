#!/usr/bin/env python3
"""
Generate WhatsApp-formatted financial report from Buku Masjid API.

Usage:
  python whatsapp_report.py
  python whatsapp_report.py --days 7
  python whatsapp_report.py --start 2026-05-10 --end 2026-05-16
  python whatsapp_report.py --mosque "MUSHOLLA EL-FATIH" --treasurer "DKM El-Fatih"
  python whatsapp_report.py --clipboard
"""

import argparse
import calendar
import subprocess
import sys
import os
from datetime import date, timedelta

from _auth import get_config, get_token, authed_get, login

DAYS = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Ahad"]
MONTHS_ID = [
    "Januari", "Februari", "Maret", "April", "Mei", "Juni",
    "Juli", "Agustus", "September", "Oktober", "November", "Desember",
]


def date_id(date_str):
    d = date.fromisoformat(date_str)
    return f"{d.day} {MONTHS_ID[d.month - 1]} {d.year}"


def day_id(date_str):
    d = date.fromisoformat(date_str)
    return DAYS[d.weekday()]


def format_idr(amount):
    """Format as Indonesian currency string: 1.234.567,00"""
    return f"{amount:,.2f}".replace(",", "\x00").replace(".", ",").replace("\x00", ".")


def parse_idr(s):
    """Parse formatted number string (Indonesian or English) to float."""
    s = str(s).strip().replace("- ", "-").replace(" ", "")
    last_dot = s.rfind(".")
    last_comma = s.rfind(",")
    if last_dot > last_comma:
        return float(s.replace(",", ""))
    else:
        return float(s.replace(".", "").replace(",", ".")) if s else 0.0


def fetch_month(base_url, token, year, month):
    """Fetch one month of transactions from the API."""
    data = authed_get(base_url, token, "/api/transactions", params={"year": year, "month": f"{month:02d}"})
    if data is None:
        return None
    txns = data.get("data", []) if isinstance(data, dict) else data
    stats = data.get("stats", {}) if isinstance(data, dict) else {}
    return txns, stats


def fetch_range(base_url, token, start_date, end_date):
    """
    Fetch transactions for an arbitrary date range.

    The API only supports year/month filtering, so we fetch each month in the
    range and filter client-side. The start balance is computed by adjusting the
    month's opening balance for any transactions that fall before start_date.
    """
    start_str = str(start_date)
    end_str = str(end_date)

    cur_month = start_date.replace(day=1)
    end_month = end_date.replace(day=1)

    all_txns_by_month = {}  # (year, month) -> list of transactions
    month_open_balance = {}  # (year, month) -> float balance before first txn of that month

    while cur_month <= end_month:
        result = fetch_month(base_url, token, cur_month.year, cur_month.month)
        if result is None:
            return None, None
        txns, stats = result
        key = (cur_month.year, cur_month.month)
        all_txns_by_month[key] = sorted(txns, key=lambda t: t["date"])
        month_open_balance[key] = parse_idr(stats.get("start_balance", "0"))

        last_day = calendar.monthrange(cur_month.year, cur_month.month)[1]
        cur_month = (cur_month.replace(day=last_day) + timedelta(days=1)).replace(day=1)

    # Saldo awal = opening balance of start_date's month + all transactions in that
    # month that fall strictly before start_date.
    start_key = (start_date.year, start_date.month)
    saldo_awal = month_open_balance.get(start_key, 0.0)
    for t in all_txns_by_month.get(start_key, []):
        if t["date"] >= start_str:
            break
        amt = t.get("amount", 0)
        saldo_awal += amt if t.get("in_out") == 1 else -amt

    # Collect filtered transactions across all fetched months
    filtered = []
    for txns in all_txns_by_month.values():
        filtered.extend(t for t in txns if start_str <= t["date"] <= end_str)
    filtered.sort(key=lambda t: t["date"])

    income_total = sum(t.get("amount", 0) for t in filtered if t.get("in_out") == 1)
    expense_total = sum(t.get("amount", 0) for t in filtered if t.get("in_out") == 0)
    saldo_akhir = saldo_awal + income_total - expense_total

    stats = {
        "start_balance": format_idr(saldo_awal),
        "end_balance": format_idr(saldo_akhir),
        "income_total": format_idr(income_total),
        "spending_total": format_idr(expense_total),
    }

    return filtered, stats


def line_label(t):
    return (t.get("description") or "").strip() or t.get("category") or "Transaksi"


def generate_message(txns, stats, start_date, end_date, mosque, address, treasurer):
    income = [t for t in txns if t.get("in_out") == 1]
    expense = [t for t in txns if t.get("in_out") == 0]

    def group_by_date(transactions):
        groups = {}
        for t in transactions:
            groups.setdefault(t["date"], []).append(t)
        return groups

    msg = "Assalamualaikum Warahmatullahi Wabarakatuh\n\n"
    msg += "*LAPORAN KEUANGAN*\n"
    msg += f"*{mosque}*\n"
    if address:
        msg += f"\U0001f54c {address}\n"
    msg += "\n"
    msg += f"*\U0001f5d3️ Periode: {date_id(str(start_date))} - {date_id(str(end_date))}*\n\n"
    msg += f"Berikut kami sampaikan rincian keuangan {mosque} untuk periode ini:\n\n"
    msg += f"*Saldo Awal:*\n*Rp {stats['start_balance']}*\n\n"

    if income:
        msg += "*\U0001f932 PEMASUKAN*\nBerikut rincian infaq yang masuk:\n\n"
        for d in sorted(group_by_date(income)):
            msg += f"*{day_id(d)}, {date_id(d)}*\n"
            for t in group_by_date(income)[d]:
                msg += f"• {line_label(t)}: Rp {format_idr(t.get('amount', 0))}\n"
            msg += "\n"
        msg += f"*Total Pemasukan: Rp {stats['income_total']}*\n\n"

    if expense:
        msg += "*\U0001f4e4 PENGELUARAN*\nBerikut rincian pengeluaran:\n\n"
        for d in sorted(group_by_date(expense)):
            msg += f"*{day_id(d)}, {date_id(d)}*\n"
            for t in group_by_date(expense)[d]:
                msg += f"• {line_label(t)}: Rp {format_idr(t.get('amount', 0))}\n"
            msg += "\n"
        msg += f"Total: *Rp {stats['spending_total']}*\n\n"

    msg += f"*\U0001f4b0 SALDO AKHIR KAS*\n*Rp {stats['end_balance']}*\n\n"
    msg += "Demikian laporan kas ini kami sampaikan.\n\n"
    msg += (
        f"Terima kasih kepada para jama'ah yang telah menyisihkan hartanya "
        f"untuk kemakmuran {mosque}. "
        "Semoga Allah SWT membalas setiap kebaikan yang diberikan.\n\n"
    )
    msg += "Jazakumullahu Khairan Katsiran.\n\n"
    msg += f"Hormat kami,\n*{treasurer}*"
    return msg


def copy_to_clipboard(text):
    for cmd in (["xclip", "-selection", "clipboard"], ["pbcopy"]):
        try:
            subprocess.run(cmd, input=text.encode(), check=True)
            return True
        except (FileNotFoundError, subprocess.CalledProcessError):
            continue
    return False


def main():
    parser = argparse.ArgumentParser(description="Generate WhatsApp financial report from Buku Masjid")
    parser.add_argument("--days", type=int, default=7, help="Last N days (default: 7)")
    parser.add_argument("--start", help="Start date YYYY-MM-DD (overrides --days)")
    parser.add_argument("--end", help="End date YYYY-MM-DD (default: today)")
    parser.add_argument("--mosque", help="Mosque name (overrides BUKU_MASJID_MOSQUE_NAME)")
    parser.add_argument("--address", help="Mosque address (overrides BUKU_MASJID_ADDRESS)")
    parser.add_argument("--treasurer", help="Treasurer name (overrides BUKU_MASJID_TREASURER)")
    parser.add_argument("--clipboard", action="store_true", help="Copy output to clipboard")
    parser.add_argument("--relogin", action="store_true", help="Force fresh login")
    args = parser.parse_args()

    end_date = date.fromisoformat(args.end) if args.end else date.today()
    start_date = date.fromisoformat(args.start) if args.start else end_date - timedelta(days=args.days - 1)

    mosque = args.mosque or os.environ.get("BUKU_MASJID_MOSQUE_NAME", "MUSHOLLA EL-FATIH")
    address = args.address or os.environ.get("BUKU_MASJID_ADDRESS", "")
    treasurer = args.treasurer or os.environ.get("BUKU_MASJID_TREASURER", "DKM Musholla El-Fatih")

    base_url, email, password, _ = get_config()
    token = get_token(base_url, email, password, args.relogin)

    txns, stats = fetch_range(base_url, token, start_date, end_date)

    if txns is None:
        token = login(base_url, email, password)
        txns, stats = fetch_range(base_url, token, start_date, end_date)

    if not txns:
        print(f"\nTidak ada transaksi dari {start_date} s/d {end_date}.\n")
        return

    message = generate_message(txns, stats, start_date, end_date, mosque, address, treasurer)
    print(message)

    if args.clipboard:
        if copy_to_clipboard(message):
            print("\n[Pesan disalin ke clipboard]")
        else:
            print("\n[Clipboard tidak tersedia: pastikan xclip (Linux) atau pbcopy (macOS) terinstal]")


if __name__ == "__main__":
    main()
