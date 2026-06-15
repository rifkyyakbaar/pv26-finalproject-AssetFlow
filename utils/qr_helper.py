import qrcode
import io
from PySide6.QtGui import QPixmap

class QRGenerator:
    @staticmethod
    def get_qr_pixmap(kode_barang, nama_barang):
        # Construct QR code data
        qr_data = f"Aplikasi AssetFlow\nKode: {kode_barang}\nNama: {nama_barang}"
        img = qrcode.make(qr_data)
        
        # Save image to in-memory buffer
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        
        # Convert to QPixmap for PySide6 display
        pixmap = QPixmap()
        pixmap.loadFromData(buffer.getvalue())
        return pixmap