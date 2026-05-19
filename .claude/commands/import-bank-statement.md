# Import Bank Statement

Import a BSI CSV bank statement into Buku Masjid.

## Steps

**1. Parse the CSV**

Run the parser and show the user a summary of what was found:
```
make import-csv ARGS="<path-to-csv>"
```

Show the parsed transactions to the user and ask them to confirm before importing.

**2. Look up reference IDs**

Before importing, fetch the current reference data using the prepared scripts only — do NOT fall back to raw curl/bash if these fail:
```
make lookup-books
make lookup-categories
make lookup-partners ARGS="<sender-name>"
make lookup-bank-accounts
```

If any lookup returns 404, stop and tell the user the endpoint is not deployed, then wait for them to fix it before continuing.

**3. Map each transaction**

For each parsed transaction, determine:

- `in_out`: `kredit` → `pemasukan` (1), `debet` → `pengeluaran` (0)
- `description`: Use judgment based on `raw_description` and `sender`:
  - BIFAST transfer from a known sender → "Infaq dari Hamba Allah"
  - QR/QRIS payment → "Infaq dari Hamba Allah - QRIS"
  - Other → use a cleaned-up version of `raw_description`
- `partner_id`: Match `sender` name to a partner from lookup (fuzzy match by first name or full name). If no match, omit.
- `category_id`: Default to "Pemasukan Infaq Lain-lain" for infaq transactions. Use judgment for others.
- `book_id`: Use the default from `.env.script` (BUKU_MASJID_BOOK_ID), or ask the user if unclear.
- `bank_account_id`: Match the bank account from lookup based on the statement source (e.g. BSI CSV → BSI account).

**4. Confirm with user**

Before inserting, print a table showing what will be imported:
```
#  Date        | Type      | Amount  | Description                   | Partner  | Category                  | Bank Account
1  2026-05-03  | Pemasukan | 10,000  | Infaq dari Hamba Allah        | Melinda  | Pemasukan Infaq Lain-lain | BSI
2  2026-05-03  | Pemasukan | 50,000  | Infaq dari Hamba Allah - QRIS | -        | Pemasukan Infaq Lain-lain | BSI
...
```

Ask: "Apakah data di atas sudah benar? Ketik 'ya' untuk melanjutkan atau berikan koreksi."

The user may say some transactions are already entered — skip those and only insert the ones they confirm.

**5. Insert transactions**

For each transaction, run:
```
make add-pemasukan ARGS="<amount> '<description>' --date <date> --book-id <id> --category-id <id> --partner-id <id> --bank-account-id <id>"
make add-pengeluaran ARGS="<amount> '<description>' --date <date> --book-id <id> --category-id <id> --bank-account-id <id>"
```

Report progress after each insertion. If one fails, report the error and continue with the rest.

**6. Summary**

After all insertions, print:
- Total inserted
- Total failed (with reasons)
- Total amount pemasukan / pengeluaran
