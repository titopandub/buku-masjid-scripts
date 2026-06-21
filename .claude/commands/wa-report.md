# Laporan WA

Buat laporan keuangan siap-paste ke WhatsApp untuk periode tertentu.

## Steps

**1. Tentukan periode**

Jika argumen `--start` dan `--end` tidak diberikan, tanyakan ke pengguna:

> "Laporan untuk periode berapa? Contoh: 2026-06-14 sampai 2026-06-20"

Gunakan tanggal yang diberikan pengguna, baik lewat argumen maupun jawaban.

**2. Generate laporan ke clipboard**

Jalankan:
```
make report-clipboard ARGS="--start <start-date> --end <end-date>"
```

**3. Konfirmasi ke pengguna**

Tampilkan isi laporan di chat, lalu beritahu bahwa laporan sudah disalin ke clipboard dan siap di-paste ke WhatsApp.
