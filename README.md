# AssetFlow

AssetFlow adalah aplikasi desktop berbasis PySide6 untuk manajemen inventaris dan sirkulasi peminjaman aset.

## Fitur Utama

- Login/Admin autentikasi dengan sesi pengguna sederhana.
- Dashboard ringkas untuk memantau jumlah barang dan transaksi peminjaman.
- Master Barang dengan CRUD, validasi input, dan status ketersediaan.
- Data Peminjaman dengan pencatatan transaksi, pengembalian, dan filter/search.
- Export data ke CSV dan PDF untuk laporan.
- SQLite lokal dengan relasi antara tabel `items` dan `loans`.

## Struktur Proyek

- `main.py` — entry point aplikasi, UI multi-halaman, login, dan navigasi.
- `requirements.txt` — daftar dependensi.
- `database/db.py` — manajemen SQLite dan operasi CRUD.
- `utils/exporter.py` — fungsi export CSV/PDF.
- `ui/style.qss` — stylesheet PySide6.

## Instalasi

1. Buat virtual environment (opsional):
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```
2. Install dependensi:
   ```bash
   pip install -r requirements.txt
   ```
3. Jalankan aplikasi:
   ```bash
   python main.py
   ```

## Akun Admin Default

- Username: `admin`
- Password: `admin123`

## Catatan

- Database SQLite dibuat otomatis di `assetflow.db` saat aplikasi dijalankan.
- UI menggunakan `QStackedWidget` untuk tampilan multi-halaman.
- Semua form melakukan validasi dasar sehingga aplikasi tidak mudah crash akibat input kosong.
