import qrcode
import os

class QRGenerator:
    @staticmethod
    def generate_qr(kode_barang, nama_barang):
        # 1. Buat folder 'qr_codes' di luar folder utils jika belum ada
        base_dir = os.path.dirname(os.path.dirname(__file__))
        save_dir = os.path.join(base_dir, 'qr_codes')
        os.makedirs(save_dir, exist_ok=True)

        # 2. Rangkai teks yang akan disembunyikan di dalam QR Code
        qr_data = f"Aplikasi AssetFlow\nKode: {kode_barang}\nNama: {nama_barang}"
        
        # 3. Generate gambarnya
        img = qrcode.make(qr_data)
        
        # 4. Simpan gambar dengan nama file sesuai kode barang
        file_path = os.path.join(save_dir, f"{kode_barang}.png")
        img.save(file_path)
        
        # Kembalikan letak file-nya agar bisa ditampilkan di UI PySide6 nanti
        return file_path