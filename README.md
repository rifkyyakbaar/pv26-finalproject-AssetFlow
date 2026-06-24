# AssetFlow: Aplikasi Manajemen Inventaris dan Peminjaman Aset

## Deskripsi Singkat
AssetFlow adalah perangkat lunak desktop multi-halaman berbasis antarmuka grafis (GUI) yang dikembangkan menggunakan **PySide6**. Aplikasi ini dirancang untuk mempermudah instansi atau kampus dalam mengelola data aset, mencatat sirkulasi peminjaman alat secara *real-time*, dan mengekspor laporan. Sistem ini ditenagai oleh basis data relasional **SQLite** lokal dan dilengkapi dengan fitur otomatisasi seperti prediksi kategori menggunakan AI, generator QR Code, serta visualisasi data analitik menggunakan Matplotlib.

---

## 👥 Tim Pengembang

Proyek ini dikembangkan untuk memenuhi tugas mata kuliah Pemrograman Visual oleh tim yang terdiri dari:

| Nama Anggota | NIM | Peran Utama |
| :--- | :--- | :--- |
| **Rifky Akbar Utomo Putra** | F1D02310149 | Backend & Database Engineer |
| **I Putu Ananta Sugiartha** | F1D02310113 | Frontend & UI Logic |
| **Ahmad Madani** | F1D02310101 | Utility & Integration |

---

## 📝 Pembagian Tugas

- **Rifky Akbar U. P. (Backend & Database):** Bertanggung jawab penuh merancang skema basis data SQLite, menulis fungsi CRUD untuk tabel `items` dan `loans`, mengamankan enkripsi *password* admin, serta memastikan logika pengurangan dan penambahan stok barang otomatis berjalan akurat di balik layar.
- **I Putu Ananta S. (Frontend & UI Logic):** Bertanggung jawab merakit arsitektur antarmuka grafis (GUI) berbasis PySide6 dengan model tata letak responsif, mengoneksikan setiap aksi tombol ke logika pemrograman, serta mengintegrasikan pustaka Matplotlib untuk menyajikan dasbor grafik analitik secara *real-time*.
- **Ahmad Madani (Utility & Integration):** Bertanggung jawab mengembangkan fitur lanjutan di luar fungsi dasar, seperti merancang algoritma tebakan otomatis kategori barang berbasis AI, membuat modul generator QR Code, serta menyusun format tata letak cetak laporan ke format CSV dan PDF (ReportLab).

---

## 📸 Screenshot Aplikasi

### 1. Halaman Login
<img width="267" height="272" alt="Login" src="https://github.com/user-attachments/assets/379aa357-7e80-4439-8b07-de80994e1b3c" />

### 2. Navigasi Menu
<img width="959" height="596" alt="Navigasi Menu" src="https://github.com/user-attachments/assets/6529582b-8288-44e5-9fe6-e0bfa84e8e58" />

### 3. Dashboard Utama & Analitik
<img width="959" height="596" alt="Dashboard" src="https://github.com/user-attachments/assets/059f478c-8736-4bc7-9fef-5e3830609cc4" />

### 4. Kelola Master Barang & Generate QR Code
<img width="959" height="597" alt="Kelola Master Barang" src="https://github.com/user-attachments/assets/8d97accc-0eb2-4a43-b7aa-1201614a1342" />

### 5. Pencatatan Data Peminjaman
<img width="959" height="599" alt="Data Peminjaman" src="https://github.com/user-attachments/assets/bed695fd-3bed-4b9d-8ab5-c4f0cd8786da" />

---

## Fitur Utama

- **Sistem Autentikasi:** Login Admin dengan manajemen sesi untuk keamanan data.
- **Dashboard Analitik:** Visualisasi *real-time* jumlah barang, status stok, dan transaksi peminjaman menggunakan Matplotlib.
- **Manajemen Inventaris (CRUD):** Tambah, edit, hapus, dan cari barang dengan validasi input yang ketat.
- **Sirkulasi Peminjaman:** Pencatatan transaksi peminjaman dan pengembalian yang terhubung langsung dengan relasi stok Master Barang.
- **AI & Utilitas Cerdas:** Prediksi kategori otomatis berbasis AI dan pembuatan *QR Code* pelabelan aset.
- **Ekspor Laporan:** Cetak data inventaris dan riwayat sirkulasi ke dalam format `CSV` atau `PDF` secara instan.

---

## Cara Menjalankan Aplikasi

Pastikan Python 3.x sudah terinstal di perangkat Anda. Ikuti langkah-langkah berikut untuk menjalankan AssetFlow secara lokal:

1. **Clone/Unduh Repositori:**
   ```bash
   git clone [https://github.com/username_kamu/assetflow.git](https://github.com/username_kamu/assetflow.git)
   cd assetflow
