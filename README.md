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

### 2. Tentang Aplikasi
<img width="959" height="598" alt="status" src="https://github.com/user-attachments/assets/65c76fca-a25c-4034-aa2d-6851c6b15d65" />

### 3. Navigasi Menu
<img width="959" height="599" alt="navigasi mnu" src="https://github.com/user-attachments/assets/ad19877c-17c2-46c9-8d2d-0cadabb9417d" />

### 4. Dashboard Utama & Analitik
<img width="959" height="599" alt="dashbord" src="https://github.com/user-attachments/assets/90cecacf-e9a3-4c66-be5b-149aa2c1438d" />

### 5. Kelola Master Barang
<img width="959" height="598" alt="kelola master brang" src="https://github.com/user-attachments/assets/005f9c31-7773-41bb-88f9-88df50cb0bea" />

### 6. Form Tambah, Edit, Hapus, dan QR Code Menu Kelola Master Barang
<img width="5040" height="2835" alt="form master barang" src="https://github.com/user-attachments/assets/790c9308-1a2f-4fd1-ac9d-02f735dd4135" />

### 7. Pencatatan Data Peminjaman
<img width="959" height="599" alt="data peminjaman" src="https://github.com/user-attachments/assets/4746b4f3-6bed-4fb5-8922-bfdbfaaa2991" />

### 9. Form Tambah dan Edit Menu Data Peminjaman
<img width="5040" height="2835" alt="form data peminjaman" src="https://github.com/user-attachments/assets/1cc956e5-7ef5-4aa5-9f8d-20f4790a9109" />

### 9. Reset Database
<img width="959" height="598" alt="reset database" src="https://github.com/user-attachments/assets/934c288d-568a-4d63-be42-189dbcd9b25b" />

### 9. Exit
<img width="959" height="599" alt="image" src="https://github.com/user-attachments/assets/f3acc064-6dc2-4d09-80f1-c50b60663ed1" />

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
