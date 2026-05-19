# buku-masjid-scripts

Operational scripts for managing a [Buku Masjid](https://github.com/nafiesl/buku-masjid) instance via its API.

## Setup

```bash
cp .env.script.example .env.script
# edit .env.script with your credentials
make setup
```

## Usage

### List transactions

```bash
make list                              # last 14 days
make list ARGS="--days 30"
make list ARGS="--start 2026-05-01 --end 2026-05-17"
make list ARGS="--type pemasukan"
```

### WhatsApp report

```bash
make report                            # last 7 days
make report ARGS="--days 14"
make report ARGS="--start 2026-05-10 --end 2026-05-16"
make report-clipboard                  # copy to clipboard (requires xclip or pbcopy)
```

### Add a transaction

```bash
make add-pemasukan ARGS="500000 'Infaq Jumat'"
make add-pengeluaran ARGS="150000 'Beli sabun' --date 2026-05-04"
make add-pemasukan ARGS="10000 'Infaq' --category-id 5 --partner-id 3"
```

### Look up reference IDs

```bash
make lookup-books
make lookup-categories
make lookup-categories ARGS="infaq"
make lookup-partners
make lookup-partners ARGS="melinda"
make lookup-bank-accounts
```

### Import bank statement CSV (BSI format)

```bash
make import-csv ARGS="path/to/Mutasi_Rekening.csv"
```

Prints a JSON array of parsed transactions to stdout for review before importing.

### Force re-login

```bash
make login
```

## Environment variables

| Variable | Required | Description |
|---|---|---|
| `BUKU_MASJID_URL` | yes | Base URL of your Buku Masjid instance |
| `BUKU_MASJID_EMAIL` | yes | Login email |
| `BUKU_MASJID_PASSWORD` | yes | Login password |
| `BUKU_MASJID_BOOK_ID` | yes | Default book (kas) ID |
| `BUKU_MASJID_MOSQUE_NAME` | no | Mosque name for WhatsApp report |
| `BUKU_MASJID_ADDRESS` | no | Mosque address for WhatsApp report |
| `BUKU_MASJID_TREASURER` | no | Treasurer name for WhatsApp report |
