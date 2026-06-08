import qrcode
import io
from PySide6.QtGui import QPixmap

class QRGenerator:
    @staticmethod
    def get_qr_pixmap(kode_barang, nama_barang):
        # 1. Rangkai teks QR Code
        qr_data = f"Aplikasi AssetFlow\nKode: {kode_barang}\nNama: {nama_barang}"
        img = qrcode.make(qr_data)
        
        # 2. Simpan gambar ke RAM (memori sementara), BUKAN ke folder
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        
        # 3. Ubah menjadi format QPixmap agar bisa dimunculkan sebagai pop-up PySide6
        pixmap = QPixmap()
        pixmap.loadFromData(buffer.getvalue())
        return pixmap