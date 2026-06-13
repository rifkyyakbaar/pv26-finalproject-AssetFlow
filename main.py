import os
import sys
import hashlib
from datetime import datetime

from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QIcon, QAction
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QComboBox,
    QTextEdit,
    QDateEdit,
    QSpinBox,
)

import matplotlib
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from database.db import DatabaseManager
from utils.exporter import export_csv, export_pdf

from utils.ai_helper import CategoryPredictor
from utils.qr_helper import QRGenerator

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database", "assetflow.db")
STYLE_PATH = os.path.join(BASE_DIR, "ui", "style.qss")


class LoginDialog(QDialog):
    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager
        self.setWindowTitle("AssetFlow - Login")
        self.setFixedSize(360, 220)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        title = QLabel("AssetFlow Admin Login")
        title.setAlignment(Qt.AlignCenter)
        title.setObjectName("titleLabel")

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.Password)

        login_button = QPushButton("Masuk")
        login_button.clicked.connect(self.try_login)

        layout.addWidget(title)
        layout.addWidget(self.username_input)
        layout.addWidget(self.password_input)
        layout.addWidget(login_button)
        layout.addStretch()

        self.setLayout(layout)

    def try_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()

        if not username or not password:
            QMessageBox.warning(self, "Login gagal", "Username dan password wajib diisi.")
            return

        if self.db_manager.authenticate_user(username, password):
            self.accept()
        else:
            QMessageBox.critical(self, "Login gagal", "Username atau password salah.")


class MainWindow(QMainWindow):
    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager
        self.ai = CategoryPredictor()
        
        self.setWindowTitle("AssetFlow - Aplikasi Manajemen Aset")
        self.resize(1200, 780)
        self.current_item_id = None
        self.current_loan_id = None
        self.init_ui()

    def init_ui(self):
        self.create_menu_bar()

        self.stack = QStackedWidget()

        self.dashboard_page = self.create_dashboard_page()
        self.items_page = self.create_items_page()
        self.loans_page = self.create_loans_page()

        self.stack.addWidget(self.dashboard_page)
        self.stack.addWidget(self.items_page)
        self.stack.addWidget(self.loans_page)

        self.setCentralWidget(self.stack)

        self.load_dashboard()
        self.load_items_table()
        self.load_loans_table()

    def create_menu_bar(self):
        menubar = self.menuBar()
        nav_menu = menubar.addMenu("☰ Navigasi Menu")
        
        action_dashboard = nav_menu.addAction("📊 Dashboard Utama")
        action_items = nav_menu.addAction("🗃️ Kelola Master Barang")
        action_loans = nav_menu.addAction("🔄 Data Peminjaman")
        
        nav_menu.addSeparator() 
        action_logout = nav_menu.addAction("🚪 Logout Sistem")
        
        action_dashboard.triggered.connect(lambda: self.stack.setCurrentWidget(self.dashboard_page))
        action_items.triggered.connect(lambda: self.stack.setCurrentWidget(self.items_page))
        action_loans.triggered.connect(lambda: self.stack.setCurrentWidget(self.loans_page))
        action_logout.triggered.connect(self.logout)

    def create_dashboard_page(self):
        page = QWidget()
        page.setObjectName("page_dashboard")
        layout = QVBoxLayout()
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        title_lbl = QLabel("Dashboard Ringkasan AssetFlow")
        title_lbl.setObjectName("titleLabel")
        layout.addWidget(title_lbl)

        capsule_layout = QHBoxLayout()
        capsule_layout.setSpacing(12)
        
        self.lbl_total_barang = QLabel("📦 Total Barang: 0")
        self.lbl_total_barang.setObjectName("lbl_total_barang")
        self.lbl_total_barang.setProperty("theme", "capsule")
        
        self.lbl_tersedia = QLabel("✅ Tersedia: 0")
        self.lbl_tersedia.setObjectName("lbl_tersedia")
        self.lbl_tersedia.setProperty("theme", "capsule")
        
        self.lbl_dipinjam = QLabel("🤝 Dipinjam: 0")
        self.lbl_dipinjam.setObjectName("lbl_dipinjam")
        self.lbl_dipinjam.setProperty("theme", "capsule")
        
        self.lbl_total_transaksi = QLabel("🔄 Total Transaksi: 0")
        self.lbl_total_transaksi.setObjectName("lbl_total_transaksi")
        self.lbl_total_transaksi.setProperty("theme", "capsule")

        capsule_layout.addWidget(self.lbl_total_barang)
        capsule_layout.addWidget(self.lbl_tersedia)
        capsule_layout.addWidget(self.lbl_dipinjam)
        capsule_layout.addWidget(self.lbl_total_transaksi)
        capsule_layout.addStretch()
        layout.addLayout(capsule_layout)

        self.chart_container = QWidget()
        self.chart_container.setObjectName("chartContainer")
        chart_inner_layout = QVBoxLayout(self.chart_container)
        chart_inner_layout.setContentsMargins(12, 12, 12, 12)

        self.figure = Figure(figsize=(10, 6), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        chart_inner_layout.addWidget(self.canvas)
        
        layout.addWidget(self.chart_container, 1)

        export_layout = QHBoxLayout()
        export_items_btn = QPushButton("📄 Export Master CSV")
        export_loans_btn = QPushButton("📄 Export Peminjaman CSV")
        export_items_pdf_btn = QPushButton("📕 Export Master PDF")
        export_loans_pdf_btn = QPushButton("📕 Export Peminjaman PDF")
        
        reset_db_btn = QPushButton("⚠️ Factory Reset")
        reset_db_btn.setObjectName("btnReset")

        export_items_btn.clicked.connect(self.export_items_csv)
        export_loans_btn.clicked.connect(self.export_loans_csv)
        export_items_pdf_btn.clicked.connect(self.export_items_pdf)
        export_loans_pdf_btn.clicked.connect(self.export_loans_pdf)
        reset_db_btn.clicked.connect(self.do_factory_reset)

        export_layout.addWidget(export_items_btn)
        export_layout.addWidget(export_loans_btn)
        export_layout.addWidget(export_items_pdf_btn)
        export_layout.addWidget(export_loans_pdf_btn)
        export_layout.addWidget(reset_db_btn)
        layout.addLayout(export_layout)
        
        page.setLayout(layout)
        return page

    def load_dashboard(self):
        summary = self.db_manager.get_dashboard_summary()
        
        self.lbl_total_barang.setText(f"📦 Total Barang: {summary['total_items']}")
        self.lbl_tersedia.setText(f"✅ Tersedia: {summary['available_items']}")
        self.lbl_dipinjam.setText(f"🤝 Dipinjam: {summary['borrowed_items']}")
        self.lbl_total_transaksi.setText(f"🔄 Total Transaksi: {summary['total_loans']} (Aktif: {summary['active_loans']})")

        self.figure.clear()
        semua_barang = self.db_manager.get_items()

        matplotlib.rcParams['text.color'] = '#1E293B'
        matplotlib.rcParams['axes.labelcolor'] = '#1E293B'
        matplotlib.rcParams['xtick.color'] = '#1E293B'
        matplotlib.rcParams['ytick.color'] = '#1E293B'

        ax1 = self.figure.add_subplot(221)
        ax1.set_facecolor('#FFFFFF')
        labels_barang = ['Tersedia', 'Dipinjam']
        sizes_barang = [summary['available_items'], summary['borrowed_items']]
        colors_barang = ['#2ECC71', '#EF4444']

        if sum(sizes_barang) == 0:
            ax1.text(0.5, 0.5, "Belum ada data", ha='center', va='center', fontweight='bold')
            ax1.axis('off')
        else:
            ax1.pie(sizes_barang, labels=labels_barang, colors=colors_barang, autopct='%1.1f%%', startangle=90, wedgeprops={'edgecolor': 'white', 'linewidth': 2})
            ax1.set_title('Proporsi Ketersediaan Aset', fontweight='bold', pad=10)

        ax2 = self.figure.add_subplot(222)
        ax2.set_facecolor('#FFFFFF')
        labels_transaksi = ['Aktif', 'Selesai']
        sizes_transaksi = [summary['active_loans'], summary['completed_loans']]
        colors_transaksi = ['#F1C40F', '#3498DB']

        bars1 = ax2.bar(labels_transaksi, sizes_transaksi, color=colors_transaksi, width=0.5, zorder=3)
        ax2.set_title('Status Peminjaman', fontweight='bold', pad=10)
        ax2.grid(axis='y', linestyle='--', alpha=0.5, zorder=0)
        ax2.spines['top'].set_visible(False)
        ax2.spines['right'].set_visible(False)
        ax2.spines['left'].set_color('#CBD5E1')
        ax2.spines['bottom'].set_color('#CBD5E1')
        
        ax2.set_ylim(0, max(sizes_transaksi) + 2 if max(sizes_transaksi) > 0 else 5)
        ax2.yaxis.set_major_locator(matplotlib.ticker.MaxNLocator(integer=True))
        ax2.bar_label(bars1, padding=3, fontweight='bold')

        ax3 = self.figure.add_subplot(212)
        ax3.set_facecolor('#FFFFFF')
        kondisi_counts = {'Baik': 0, 'Rusak Ringan': 0, 'Rusak Berat': 0}
        for item in semua_barang:
            knd = item.get('condition', '')
            if knd in kondisi_counts:
                kondisi_counts[knd] += 1
                
        labels_kondisi = list(kondisi_counts.keys())
        sizes_kondisi = list(kondisi_counts.values())
        colors_kondisi = ['#27AE60', '#F39C12', '#C0392B']
        
        bars2 = ax3.bar(labels_kondisi, sizes_kondisi, color=colors_kondisi, width=0.4, zorder=3)
        ax3.set_title('Rekapitulasi Kondisi Fisik Aset', fontweight='bold', pad=10)
        ax3.grid(axis='y', linestyle='--', alpha=0.5, zorder=0)
        ax3.spines['top'].set_visible(False)
        ax3.spines['right'].set_visible(False)
        ax3.spines['left'].set_color('#CBD5E1')
        ax3.spines['bottom'].set_color('#CBD5E1')
        
        ax3.set_ylim(0, max(sizes_kondisi) + 3 if max(sizes_kondisi) > 0 else 5)
        ax3.yaxis.set_major_locator(matplotlib.ticker.MaxNLocator(integer=True))
        ax3.bar_label(bars2, padding=3, fontweight='bold')

        self.figure.patch.set_facecolor('#FFFFFF')
        self.figure.tight_layout()
        self.canvas.draw()

    def create_items_page(self):
        page = QWidget()
        main_layout = QHBoxLayout()

        left_widget = QGroupBox("Form Input Barang")
        left_widget.setMaximumWidth(350)
        left_layout = QVBoxLayout()

        self.item_name_input = QLineEdit()
        self.item_category_input = QLineEdit()
        self.item_category_input.setPlaceholderText("Akan ditebak AI otomatis...")
        self.item_quantity_input = QSpinBox()
        self.item_quantity_input.setMinimum(1)
        self.item_condition_input = QComboBox()
        self.item_condition_input.addItems(["Baik", "Rusak Ringan", "Rusak Berat"])
        self.item_location_input = QLineEdit()
        self.item_description_input = QTextEdit()
        self.item_description_input.setFixedHeight(70)

        self.item_name_input.textChanged.connect(self.auto_predict_category)

        left_layout.addWidget(QLabel("Nama Barang"))
        left_layout.addWidget(self.item_name_input)
        left_layout.addWidget(QLabel("Kategori"))
        left_layout.addWidget(self.item_category_input)
        left_layout.addWidget(QLabel("Jumlah"))
        left_layout.addWidget(self.item_quantity_input)
        left_layout.addWidget(QLabel("Kondisi"))
        left_layout.addWidget(self.item_condition_input)
        left_layout.addWidget(QLabel("Lokasi"))
        left_layout.addWidget(self.item_location_input)
        left_layout.addWidget(QLabel("Keterangan"))
        left_layout.addWidget(self.item_description_input)

        btn_row1 = QHBoxLayout()
        add_button = QPushButton("➕ Tambah")
        add_button.setObjectName("btn_tambah_barang")
        update_button = QPushButton("✏️ Perbarui")
        update_button.setObjectName("btn_update_barang")
        btn_row1.addWidget(add_button)
        btn_row1.addWidget(update_button)

        btn_row2 = QHBoxLayout()
        delete_button = QPushButton("🗑️ Hapus")
        delete_button.setObjectName("btn_hapus_barang")
        reset_button = QPushButton("🔄 Bersihkan")
        reset_button.setObjectName("btn_clear_barang")
        btn_row2.addWidget(delete_button)
        btn_row2.addWidget(reset_button)

        generate_qr_button = QPushButton("🔲 Buat QR Code")
        generate_qr_button.setObjectName("btn_qr_barang")

        add_button.clicked.connect(self.add_item)
        update_button.clicked.connect(self.update_item)
        delete_button.clicked.connect(self.delete_item)
        reset_button.clicked.connect(self.clear_item_form)
        generate_qr_button.clicked.connect(self.generate_qr_code)

        left_layout.addLayout(btn_row1)
        left_layout.addLayout(btn_row2)
        left_layout.addWidget(generate_qr_button)
        left_layout.addStretch()

        left_widget.setLayout(left_layout)

        right_widget = QWidget()
        right_layout = QVBoxLayout()

        search_layout = QHBoxLayout()
        self.item_search_input = QLineEdit()
        self.item_search_input.setPlaceholderText("Cari nama, kategori, kondisi, lokasi...")
        self.item_filter_status = QComboBox()
        self.item_filter_status.addItems(["Semua", "Tersedia", "Dipinjam"])
        search_button = QPushButton("🔍 Cari")
        clear_search_button = QPushButton("Reset")

        search_button.clicked.connect(self.load_items_table)
        clear_search_button.clicked.connect(self.reset_item_search)

        search_layout.addWidget(self.item_search_input)
        search_layout.addWidget(self.item_filter_status)
        search_layout.addWidget(search_button)
        search_layout.addWidget(clear_search_button)

        self.items_table = QTableWidget()
        self.items_table.setColumnCount(7)
        self.items_table.setHorizontalHeaderLabels([
            "ID", "Nama Barang", "Kategori", "Jumlah", "Kondisi", "Lokasi", "Status"
        ])
        self.items_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.items_table.horizontalHeader().setStretchLastSection(True)
        self.items_table.cellClicked.connect(self.load_item_form)

        right_layout.addLayout(search_layout)
        right_layout.addWidget(self.items_table)
        right_widget.setLayout(right_layout)

        main_layout.addWidget(left_widget)
        main_layout.addWidget(right_widget, 1)

        page.setLayout(main_layout)
        return page

    def create_loans_page(self):
        page = QWidget()
        main_layout = QHBoxLayout()

        left_widget = QGroupBox("Form Peminjaman")
        left_widget.setMaximumWidth(350)
        left_layout = QVBoxLayout()

        self.loan_item_id_input = QLineEdit()
        self.loan_item_id_input.setReadOnly(True)
        self.loan_item_id_input.setPlaceholderText("Pilih dari tabel...")
        
        self.loan_item_input = QLineEdit()
        self.loan_item_input.setReadOnly(True)
        
        self.borrower_name_input = QLineEdit()
        self.borrower_id_input = QLineEdit()
        self.loan_quantity_input = QSpinBox()
        self.loan_quantity_input.setMinimum(1)
        
        self.borrow_date_input = QDateEdit(QDate.currentDate())
        self.borrow_date_input.setCalendarPopup(True)
        self.return_date_input = QDateEdit(QDate.currentDate())
        self.return_date_input.setCalendarPopup(True)
        
        self.loan_status_input = QComboBox()
        self.loan_status_input.addItems(["Dipinjam", "Selesai"])
        self.loan_notes_input = QTextEdit()
        self.loan_notes_input.setFixedHeight(50)

        left_layout.addWidget(QLabel("ID Barang (Otomatis)"))
        left_layout.addWidget(self.loan_item_id_input)
        left_layout.addWidget(QLabel("Nama Barang"))
        left_layout.addWidget(self.loan_item_input)
        left_layout.addWidget(QLabel("Nama Peminjam"))
        left_layout.addWidget(self.borrower_name_input)
        left_layout.addWidget(QLabel("NIM / ID Peminjam"))
        left_layout.addWidget(self.borrower_id_input)
        left_layout.addWidget(QLabel("Jumlah Pinjam"))
        left_layout.addWidget(self.loan_quantity_input)
        
        date_layout = QHBoxLayout()
        date_box1 = QVBoxLayout()
        date_box1.addWidget(QLabel("Tgl Pinjam"))
        date_box1.addWidget(self.borrow_date_input)
        date_box2 = QVBoxLayout()
        date_box2.addWidget(QLabel("Tgl Kembali"))
        date_box2.addWidget(self.return_date_input)
        date_layout.addLayout(date_box1)
        date_layout.addLayout(date_box2)
        left_layout.addLayout(date_layout)

        left_layout.addWidget(QLabel("Status Peminjaman"))
        left_layout.addWidget(self.loan_status_input)
        left_layout.addWidget(QLabel("Catatan"))
        left_layout.addWidget(self.loan_notes_input)

        btn_row1 = QHBoxLayout()
        add_loan_button = QPushButton("➕ Tambah")
        update_loan_button = QPushButton("✏️ Perbarui")
        btn_row1.addWidget(add_loan_button)
        btn_row1.addWidget(update_loan_button)

        btn_row2 = QHBoxLayout()
        mark_return_button = QPushButton("✅ Tandai Selesai")
        reset_loan_form_button = QPushButton("🔄 Bersihkan")
        btn_row2.addWidget(mark_return_button)
        btn_row2.addWidget(reset_loan_form_button)

        add_loan_button.clicked.connect(self.add_loan)
        update_loan_button.clicked.connect(self.update_loan)
        mark_return_button.clicked.connect(self.mark_returned)
        reset_loan_form_button.clicked.connect(self.clear_loan_form)

        left_layout.addLayout(btn_row1)
        left_layout.addLayout(btn_row2)
        left_layout.addStretch()

        left_widget.setLayout(left_layout)

        right_widget = QWidget()
        right_layout = QVBoxLayout()

        filter_layout = QHBoxLayout()
        self.loan_search_input = QLineEdit()
        self.loan_search_input.setPlaceholderText("Cari nama peminjam, barang, status...")
        self.loan_filter_status = QComboBox()
        self.loan_filter_status.addItems(["Semua", "Dipinjam", "Selesai"])
        loan_search_button = QPushButton("🔍 Cari")
        loan_reset_button = QPushButton("Reset")

        loan_search_button.clicked.connect(self.load_loans_table)
        loan_reset_button.clicked.connect(self.reset_loan_search)

        filter_layout.addWidget(self.loan_search_input)
        filter_layout.addWidget(self.loan_filter_status)
        filter_layout.addWidget(loan_search_button)
        filter_layout.addWidget(loan_reset_button)

        self.loans_table = QTableWidget()
        self.loans_table.setColumnCount(8)
        self.loans_table.setHorizontalHeaderLabels([
            "ID", "Nama Barang", "Nama Peminjam", "NIM/ID", 
            "Jumlah", "Tgl Pinjam", "Tgl Kembali", "Status"
        ])
        self.loans_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.loans_table.horizontalHeader().setStretchLastSection(True)
        self.loans_table.cellClicked.connect(self.load_loan_form)

        right_layout.addLayout(filter_layout)
        right_layout.addWidget(self.loans_table)
        right_widget.setLayout(right_layout)

        main_layout.addWidget(left_widget)
        main_layout.addWidget(right_widget, 1)

        page.setLayout(main_layout)
        return page

    def auto_predict_category(self, text):
        kategori = self.ai.predict_category(text)
        self.item_category_input.setText(kategori)

    def generate_qr_code(self):
        if not self.current_item_id:
            QMessageBox.warning(self, "Peringatan", "Pilih barang dari tabel terlebih dahulu untuk dibuatkan QR Code.")
            return
            
        kode = f"ITEM-{self.current_item_id}"
        nama = self.item_name_input.text().strip()
        
        pixmap = QRGenerator.get_qr_pixmap(kode, nama)
        
        dialog = QDialog(self)
        dialog.setWindowTitle(f"QR Code - {nama}")
        layout = QVBoxLayout()
        
        lbl_img = QLabel()
        lbl_img.setPixmap(pixmap)
        lbl_img.setAlignment(Qt.AlignCenter)
        
        btn_save = QPushButton("💾 Simpan Gambar")
        btn_save.clicked.connect(lambda: self.save_qr_manual(pixmap, kode))
        
        layout.addWidget(lbl_img)
        layout.addWidget(btn_save)
        dialog.setLayout(layout)
        dialog.exec()

    def save_qr_manual(self, pixmap, kode):
        path, _ = QFileDialog.getSaveFileName(self, "Simpan QR Code", f"{kode}.png", "PNG Files (*.png)")
        if path:
            pixmap.save(path, "PNG")
            QMessageBox.information(self, "Sukses", "Gambar QR Code berhasil disimpan!")

    def logout(self):
        self.close()

    def load_items_table(self):
        query = self.item_search_input.text().strip()
        status_filter = self.item_filter_status.currentText()
        items = self.db_manager.search_items(query, status_filter)

        self.items_table.setRowCount(len(items))
        for row_index, item in enumerate(items):
            self.items_table.setItem(row_index, 0, QTableWidgetItem(str(item["id"])))
            self.items_table.setItem(row_index, 1, QTableWidgetItem(item["name"]))
            self.items_table.setItem(row_index, 2, QTableWidgetItem(item["category"]))
            self.items_table.setItem(row_index, 3, QTableWidgetItem(str(item["quantity"])))
            self.items_table.setItem(row_index, 4, QTableWidgetItem(item["condition"]))
            self.items_table.setItem(row_index, 5, QTableWidgetItem(item["location"]))
            self.items_table.setItem(row_index, 6, QTableWidgetItem(item["status"]))

    def reset_item_search(self):
        self.item_search_input.clear()
        self.item_filter_status.setCurrentIndex(0)
        self.load_items_table()

    def load_item_form(self, row, _column):
        item_id = self.items_table.item(row, 0).text()
        item = self.db_manager.get_item_by_id(int(item_id))
        if not item:
            return

        self.current_item_id = item["id"]
        
        self.item_name_input.textChanged.disconnect(self.auto_predict_category)
        self.item_name_input.setText(item["name"])
        self.item_category_input.setText(item["category"])
        self.item_name_input.textChanged.connect(self.auto_predict_category)
        
        self.item_quantity_input.setValue(item["quantity"])
        index = self.item_condition_input.findText(item["condition"])
        self.item_condition_input.setCurrentIndex(index if index >= 0 else 0)
        self.item_location_input.setText(item["location"])
        self.item_description_input.setPlainText(item["description"])

        self.loan_item_id_input.setText(str(item["id"]))
        self.loan_item_input.setText(item["name"])

    def clear_item_form(self):
        self.current_item_id = None
        self.item_name_input.clear()
        self.item_category_input.clear()
        self.item_quantity_input.setValue(1)
        self.item_condition_input.setCurrentIndex(0)
        self.item_location_input.clear()
        self.item_description_input.clear()
        self.items_table.clearSelection()

    def add_item(self):
        name = self.item_name_input.text().strip()
        category = self.item_category_input.text().strip()
        quantity = self.item_quantity_input.value()
        condition = self.item_condition_input.currentText()
        location = self.item_location_input.text().strip()
        description = self.item_description_input.toPlainText().strip()

        if not name or not category or not location:
            QMessageBox.warning(self, "Validasi", "Nama, kategori, dan lokasi tidak boleh kosong.")
            return

        self.db_manager.add_item(name, category, quantity, condition, location, description)
        self.load_items_table()
        self.load_dashboard()
        QMessageBox.information(self, "Sukses", "Barang berhasil ditambahkan.")
        self.clear_item_form()

    def update_item(self):
        if not self.current_item_id:
            QMessageBox.warning(self, "Peringatan", "Pilih barang yang ingin diperbarui terlebih dahulu.")
            return

        name = self.item_name_input.text().strip()
        category = self.item_category_input.text().strip()
        quantity = self.item_quantity_input.value()
        condition = self.item_condition_input.currentText()
        location = self.item_location_input.text().strip()
        description = self.item_description_input.toPlainText().strip()

        if not name or not category or not location:
            QMessageBox.warning(self, "Validasi", "Nama, kategori, dan lokasi tidak boleh kosong.")
            return

        self.db_manager.update_item(self.current_item_id, name, category, quantity, condition, location, description)
        self.load_items_table()
        self.load_dashboard()
        QMessageBox.information(self, "Sukses", "Data barang berhasil diperbarui.")
        self.clear_item_form()

    def delete_item(self):
        if not self.current_item_id:
            QMessageBox.warning(self, "Peringatan", "Pilih barang yang ingin dihapus terlebih dahulu.")
            return

        confirm = QMessageBox.question(self, "Konfirmasi", "Yakin ingin menghapus barang ini?", QMessageBox.Yes | QMessageBox.No)
        if confirm != QMessageBox.Yes:
            return

        self.db_manager.delete_item(self.current_item_id)
        self.load_items_table()
        self.load_dashboard()
        QMessageBox.information(self, "Sukses", "Barang berhasil dihapus.")
        self.clear_item_form()

    def load_loans_table(self):
        query = self.loan_search_input.text().strip()
        status_filter = self.loan_filter_status.currentText()
        loans = self.db_manager.search_loans(query, status_filter)

        self.loans_table.setRowCount(len(loans))
        for row_index, loan in enumerate(loans):
            self.loans_table.setItem(row_index, 0, QTableWidgetItem(str(loan["id"])))
            self.loans_table.setItem(row_index, 1, QTableWidgetItem(loan["item_name"]))
            self.loans_table.setItem(row_index, 2, QTableWidgetItem(loan["borrower_name"]))
            self.loans_table.setItem(row_index, 3, QTableWidgetItem(loan["borrower_id"]))
            self.loans_table.setItem(row_index, 4, QTableWidgetItem(str(loan["quantity"])))
            self.loans_table.setItem(row_index, 5, QTableWidgetItem(loan["borrow_date"]))
            self.loans_table.setItem(row_index, 6, QTableWidgetItem(loan["return_date"]))
            self.loans_table.setItem(row_index, 7, QTableWidgetItem(loan["status"]))

    def reset_loan_search(self):
        self.loan_search_input.clear()
        self.loan_filter_status.setCurrentIndex(0)
        self.load_loans_table()

    def load_loan_form(self, row, _column):
        loan_id = self.loans_table.item(row, 0).text()
        loan = self.db_manager.get_loan_by_id(int(loan_id))
        if not loan:
            return

        self.current_loan_id = loan["id"]
        self.loan_item_id_input.setText(str(loan["item_id"]))
        self.loan_item_input.setText(loan["item_name"])
        self.borrower_name_input.setText(loan["borrower_name"])
        self.borrower_id_input.setText(loan["borrower_id"])
        self.loan_quantity_input.setValue(loan["quantity"])
        self.borrow_date_input.setDate(QDate.fromString(loan["borrow_date"], "yyyy-MM-dd"))
        self.return_date_input.setDate(QDate.fromString(loan["return_date"], "yyyy-MM-dd"))
        index = self.loan_status_input.findText(loan["status"])
        self.loan_status_input.setCurrentIndex(index if index >= 0 else 0)
        self.loan_notes_input.setPlainText(loan["notes"] or "")

    def clear_loan_form(self):
        self.current_loan_id = None
        self.loan_item_id_input.clear()
        self.loan_item_input.clear()
        self.borrower_name_input.clear()
        self.borrower_id_input.clear()
        self.loan_quantity_input.setValue(1)
        self.borrow_date_input.setDate(QDate.currentDate())
        self.return_date_input.setDate(QDate.currentDate())
        self.loan_status_input.setCurrentIndex(0)
        self.loan_notes_input.clear()
        self.loans_table.clearSelection()

    def add_loan(self):
        item_id_text = self.loan_item_id_input.text().strip()
        borrower_name = self.borrower_name_input.text().strip()
        borrower_id = self.borrower_id_input.text().strip()
        quantity = self.loan_quantity_input.value()
        borrow_date = self.borrow_date_input.date().toString("yyyy-MM-dd")
        return_date = self.return_date_input.date().toString("yyyy-MM-dd")
        status = self.loan_status_input.currentText()
        notes = self.loan_notes_input.toPlainText().strip()

        if not item_id_text:
            QMessageBox.warning(self, "Validasi", "Pilih barang dari tabel master item terlebih dahulu.")
            return
        if not borrower_name or not borrower_id:
            QMessageBox.warning(self, "Validasi", "Nama dan ID peminjam tidak boleh kosong.")
            return

        item_id = int(item_id_text)
        success, message = self.db_manager.add_loan(item_id, borrower_name, borrower_id, quantity, borrow_date, return_date, status, notes)
        if not success:
            QMessageBox.warning(self, "Gagal", message)
            return

        self.load_loans_table()
        self.load_items_table()
        self.load_dashboard()
        QMessageBox.information(self, "Sukses", "Transaksi peminjaman berhasil ditambahkan.")
        self.clear_loan_form()

    def update_loan(self):
        if not self.current_loan_id:
            QMessageBox.warning(self, "Peringatan", "Pilih transaksi yang ingin diperbarui terlebih dahulu.")
            return

        borrower_name = self.borrower_name_input.text().strip()
        borrower_id = self.borrower_id_input.text().strip()
        quantity = self.loan_quantity_input.value()
        borrow_date = self.borrow_date_input.date().toString("yyyy-MM-dd")
        return_date = self.return_date_input.date().toString("yyyy-MM-dd")
        status = self.loan_status_input.currentText()
        notes = self.loan_notes_input.toPlainText().strip()

        if not borrower_name or not borrower_id:
            QMessageBox.warning(self, "Validasi", "Nama dan ID peminjam tidak boleh kosong.")
            return

        self.db_manager.update_loan(self.current_loan_id, borrower_name, borrower_id, quantity, borrow_date, return_date, status, notes)
        self.load_loans_table()
        self.load_items_table()
        self.load_dashboard()
        QMessageBox.information(self, "Sukses", "Transaksi peminjaman berhasil diperbarui.")
        self.clear_loan_form()

    def mark_returned(self):
        if not self.current_loan_id:
            QMessageBox.warning(self, "Peringatan", "Pilih transaksi terlebih dahulu.")
            return

        self.db_manager.update_loan_status(self.current_loan_id, "Selesai")
        self.load_loans_table()
        self.load_items_table()
        self.load_dashboard()
        QMessageBox.information(self, "Sukses", "Transaksi peminjaman berhasil ditandai selesai.")
        self.clear_loan_form()

    def do_factory_reset(self):
        confirm = QMessageBox.warning(
            self, 
            "PERINGATAN BAHAYA!", 
            "Yakin ingin MENGHAPUS SEMUA DATA barang dan peminjaman secara permanen?\n\nID juga akan direset dari angka 1. Tindakan ini TIDAK BISA dibatalkan!", 
            QMessageBox.Yes | QMessageBox.No
        )
        
        if confirm == QMessageBox.Yes:
            success, msg = self.db_manager.reset_database()
            if success:
                QMessageBox.information(self, "Reset Berhasil", msg)
                self.load_dashboard()
                self.load_items_table()
                self.load_loans_table()
            else:
                QMessageBox.critical(self, "Gagal", msg)

    def export_items_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "Simpan CSV Master Barang", "master_barang.csv", "CSV Files (*.csv)")
        if not path:
            return
        rows = self.db_manager.get_items()
        export_csv(rows, path, "master_barang")
        QMessageBox.information(self, "Sukses", f"Master barang diekspor ke {path}")

    def export_loans_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "Simpan CSV Peminjaman", "peminjaman.csv", "CSV Files (*.csv)")
        if not path:
            return
        rows = self.db_manager.get_loans()
        export_csv(rows, path, "peminjaman")
        QMessageBox.information(self, "Sukses", f"Data peminjaman diekspor ke {path}")

    def export_items_pdf(self):
        path, _ = QFileDialog.getSaveFileName(self, "Simpan PDF Master Barang", "master_barang.pdf", "PDF Files (*.pdf)")
        if not path:
            return
        rows = self.db_manager.get_items()
        export_pdf(rows, path, "Laporan Master Barang")
        QMessageBox.information(self, "Sukses", f"Master barang diekspor ke {path}")

    def export_loans_pdf(self):
        path, _ = QFileDialog.getSaveFileName(self, "Simpan PDF Peminjaman", "peminjaman.pdf", "PDF Files (*.pdf)")
        if not path:
            return
        rows = self.db_manager.get_loans()
        export_pdf(rows, path, "Laporan Peminjaman")
        QMessageBox.information(self, "Sukses", f"Data peminjaman diekspor ke {path}")


def load_stylesheet(app):
    if os.path.exists(STYLE_PATH):
        with open(STYLE_PATH, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())


def main():
    app = QApplication(sys.argv)
    load_stylesheet(app)

    db_manager = DatabaseManager(DB_PATH)
    login = LoginDialog(db_manager)
    if login.exec() == QDialog.Accepted:
        window = MainWindow(db_manager)
        window.show()
        sys.exit(app.exec())


if __name__ == "__main__":
    main()