import qrcode
import io
from PySide6.QtGui import QPixmap

class QRGenerator:
    @staticmethod
    def get_qr_pixmap(kode_barang, nama_barang):
        qr_data = f"Aplikasi AssetFlow\nKode: {kode_barang}\nNama: {nama_barang}"
        img = qrcode.make(qr_data)
        
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        
        pixmap = QPixmap()
        pixmap.loadFromData(buffer.getvalue())
        return pixmap