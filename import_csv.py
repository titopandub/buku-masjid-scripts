#!/usr/bin/env python3
"""
Parse a BSI bank statement CSV into structured JSON for review before importing.

Usage:
  python import_csv.py path/to/Mutasi_Rekening.csv

Output: JSON array printed to stdout, one transaction per line.
Each item:
  {
    "date": "2026-05-03",
    "amount": 10000,
    "type": "kredit" | "debet",
    "sender": "MELINDA ALVIONITA SUMARNO" | null,
    "sender_bank": "Bank Seabank" | null,
    "raw_description": "BIFAST - TRF Dari ...",
    "kode": "213"
  }
"""

import csv
import json
import sys
from pathlib import Path


def parse_amount(value: str) -> int:
    """Convert '10,000.00' or '10,000.00-' to 10000."""
    if not value or not value.strip():
        return 0
    v = value.strip().replace(",", "")
    if v.endswith("-"):
        v = "-" + v[:-1]
    return int(float(v))


def parse_date(waktu: str) -> str:
    """Convert '03-05-2026 08.13' to '2026-05-03'."""
    date_part = waktu.strip().split(" ")[0]   # '03-05-2026'
    day, month, year = date_part.split("-")
    return f"{year}-{month}-{day}"


def parse_csv(file_path: str) -> list:
    path = Path(file_path)
    if not path.exists():
        sys.exit(f"File not found: {file_path}")

    transactions = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        header_found = False
        headers = []

        for row in reader:
            if not row:
                continue

            # detect the actual column header row
            if not header_found:
                if row[0].strip().startswith("Waktu Transaksi"):
                    headers = [h.strip() for h in row]
                    header_found = True
                continue

            if len(row) < len(headers):
                continue

            record = dict(zip(headers, [v.strip() for v in row]))
            debet = parse_amount(record.get("Debet", ""))
            kredit = parse_amount(record.get("Kredit", ""))

            if debet == 0 and kredit == 0:
                continue

            transactions.append({
                "date": parse_date(record["Waktu Transaksi"]),
                "amount": kredit if kredit > 0 else debet,
                "type": "kredit" if kredit > 0 else "debet",
                "sender": record.get("Nama Pengirim") or None,
                "sender_bank": record.get("Bank Pengirim") or None,
                "raw_description": record.get("Deskripsi", ""),
                "kode": record.get("Kode", ""),
            })

    return transactions


def main():
    if len(sys.argv) < 2:
        sys.exit("Usage: python import_csv.py <path-to-csv>")

    transactions = parse_csv(sys.argv[1])
    print(json.dumps(transactions, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
