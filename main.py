import os
import sys
import hashlib
from datetime import datetime

from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QIcon, QAction, QColor
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
    QGraphicsDropShadowEffect,
    QFrame,
    QHeaderView,
    QSizePolicy,
    QScrollArea,
    QCompleter,
    QTabWidget,
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


class ItemBrowseDialog(QDialog):
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.selected_item_id = None
        self.selected_item_name = None
        self.setWindowTitle("Katalog Barang - Pilih Barang")
        self.resize(700, 450)
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # Header/Title
        title = QLabel("Katalog Barang Tersedia")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #073B3A;")
        layout.addWidget(title)
        
        # Search bar
        search_layout = QHBoxLayout()
        search_layout.setSpacing(8)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Cari nama barang, kategori, lokasi, kondisi...")
        self.search_input.setMinimumHeight(30)
        self.search_input.textChanged.connect(self.load_items)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)
        
        # Table of items
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID", "Nama Barang", "Kategori", "Stok Tersedia", "Kondisi", "Lokasi"])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.cellDoubleClicked.connect(self.select_item_and_close)
        
        layout.addWidget(self.table)
        
        # Buttons layout
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        btn_layout.addStretch()
        
        self.btn_select = QPushButton("Pilih Barang")
        self.btn_select.setObjectName("primaryBtn")
        self.btn_select.setStyleSheet("padding: 8px 20px; font-weight: bold;")
        self.btn_select.clicked.connect(self.select_item_and_close)
        
        self.btn_cancel = QPushButton("Batal")
        self.btn_cancel.setObjectName("resetFormBtn")
        self.btn_cancel.setStyleSheet("background-color: #CFD8DC; color: #37474F; padding: 8px 20px; font-weight: bold; border: none; border-radius: 10px;")
        self.btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_select)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
        self.load_items()
        
    def load_items(self):
        query = self.search_input.text().strip()
        items = self.db_manager.search_items(query, "Tersedia")
        
        # Filter: only display items that have quantity > 0
        filtered_items = [item for item in items if item["quantity"] > 0]
        
        self.table.setRowCount(len(filtered_items))
        for row_idx, item in enumerate(filtered_items):
            self.table.setItem(row_idx, 0, QTableWidgetItem(str(item["id"])))
            self.table.setItem(row_idx, 1, QTableWidgetItem(item["name"]))
            self.table.setItem(row_idx, 2, QTableWidgetItem(item["category"]))
            self.table.setItem(row_idx, 3, QTableWidgetItem(str(item["quantity"])))
            self.table.setItem(row_idx, 4, QTableWidgetItem(item["condition"]))
            self.table.setItem(row_idx, 5, QTableWidgetItem(item["location"]))
            
    def select_item_and_close(self):
        selected_ranges = self.table.selectedRanges()
        if not selected_ranges:
            QMessageBox.warning(self, "Peringatan", "Silakan pilih salah satu barang terlebih dahulu.")
            return
        row = selected_ranges[0].topRow()
        self.selected_item_id = int(self.table.item(row, 0).text())
        self.selected_item_name = self.table.item(row, 1).text()
        self.accept()


class LoginDialog(QDialog):
    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager
        self.setWindowTitle("AssetFlow - Login")
        self.setFixedSize(360, 340)
        self.init_ui()

    def init_ui(self):
        # Dialog main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # Vertical card wrapper
        card = QFrame()
        card.setObjectName("mainCard") # Matches the soft-UI glassmorphism card style in style.qss!
        
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 25, 20, 25)
        card_layout.setSpacing(12)
        
        # Logo/Icon
        logo = QLabel("📦")
        logo.setStyleSheet("font-size: 40px; margin-bottom: 0px;")
        logo.setAlignment(Qt.AlignCenter)
        
        # Centered app name
        title = QLabel("AssetFlow")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #073B3A; margin-bottom: 8px;")
        title.setAlignment(Qt.AlignCenter)

        # Placeholders
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        self.username_input.setMinimumHeight(32)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setMinimumHeight(32)

        # Login button
        login_button = QPushButton("Masuk")
        login_button.setObjectName("primaryBtn")
        login_button.setMinimumHeight(34)
        login_button.setStyleSheet("font-weight: bold; font-size: 13px; margin-top: 8px;")
        login_button.clicked.connect(self.try_login)

        # Add to card layout
        card_layout.addWidget(logo)
        card_layout.addWidget(title)
        card_layout.addWidget(self.username_input)
        card_layout.addWidget(self.password_input)
        card_layout.addWidget(login_button)
        card_layout.addStretch()

        # Drop shadow for card
        shadow = QGraphicsDropShadowEffect(card)
        shadow.setBlurRadius(25)
        shadow.setXOffset(0)
        shadow.setYOffset(8)
        shadow.setColor(QColor(0, 80, 80, 15))
        card.setGraphicsEffect(shadow)

        main_layout.addWidget(card)

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
        self.resize(1160, 700)
        self.setMinimumSize(1080, 700)
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
        
        action_dashboard.triggered.connect(self.show_dashboard_page)
        action_items.triggered.connect(self.show_items_page)
        action_loans.triggered.connect(self.show_loans_page)
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
        self.lbl_total_barang.setObjectName("miniBadge")
        self.lbl_total_barang.setProperty("theme", "capsule")
        
        self.lbl_tersedia = QLabel("✅ Tersedia: 0")
        self.lbl_tersedia.setObjectName("miniBadge")
        self.lbl_tersedia.setProperty("theme", "capsule")
        
        self.lbl_dipinjam = QLabel("🤝 Dipinjam: 0")
        self.lbl_dipinjam.setObjectName("miniBadge")
        self.lbl_dipinjam.setProperty("theme", "capsule")
        
        self.lbl_total_transaksi = QLabel("🔄 Total Transaksi: 0")
        self.lbl_total_transaksi.setObjectName("miniBadge")
        self.lbl_total_transaksi.setProperty("theme", "capsule")

        capsule_layout.addWidget(self.lbl_total_barang)
        capsule_layout.addWidget(self.lbl_tersedia)
        capsule_layout.addWidget(self.lbl_dipinjam)
        capsule_layout.addWidget(self.lbl_total_transaksi)
        capsule_layout.addStretch()
        layout.addLayout(capsule_layout)

        # Apply capsule shadows
        for lbl in [self.lbl_total_barang, self.lbl_tersedia, self.lbl_dipinjam, self.lbl_total_transaksi]:
            shadow = QGraphicsDropShadowEffect(lbl)
            shadow.setBlurRadius(15)
            shadow.setXOffset(0)
            shadow.setYOffset(4)
            shadow.setColor(QColor(0, 80, 80, 15))
            lbl.setGraphicsEffect(shadow)

        self.chart_container = QFrame()
        self.chart_container.setObjectName("mainCard")
        chart_inner_layout = QVBoxLayout(self.chart_container)
        chart_inner_layout.setContentsMargins(12, 12, 12, 12)

        # Apply chart container shadow
        shadow_chart = QGraphicsDropShadowEffect(self.chart_container)
        shadow_chart.setBlurRadius(25)
        shadow_chart.setXOffset(0)
        shadow_chart.setYOffset(8)
        shadow_chart.setColor(QColor(0, 80, 80, 15))
        self.chart_container.setGraphicsEffect(shadow_chart)

        self.figure = Figure(figsize=(10, 6), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        chart_inner_layout.addWidget(self.canvas)
        
        layout.addWidget(self.chart_container, 1)

        export_layout = QHBoxLayout()
        export_items_btn = QPushButton("📄 Export Master CSV")
        export_items_btn.setObjectName("exportBtn")
        export_loans_btn = QPushButton("📄 Export Peminjaman CSV")
        export_loans_btn.setObjectName("exportBtn")
        export_items_pdf_btn = QPushButton("📕 Export Master PDF")
        export_items_pdf_btn.setObjectName("exportBtn")
        export_loans_pdf_btn = QPushButton("📕 Export Peminjaman PDF")
        export_loans_pdf_btn.setObjectName("exportBtn")
        
        reset_db_btn = QPushButton("⚠️ Factory Reset")
        reset_db_btn.setObjectName("resetBtn")

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

        # Configure matplotlib style
        matplotlib.rcParams['text.color'] = '#6E8B93'
        matplotlib.rcParams['axes.labelcolor'] = '#6E8B93'
        matplotlib.rcParams['xtick.color'] = '#6E8B93'
        matplotlib.rcParams['ytick.color'] = '#6E8B93'
        matplotlib.rcParams['font.family'] = 'sans-serif'
        matplotlib.rcParams['font.sans-serif'] = ['Plus Jakarta Sans', 'Inter', 'Segoe UI', 'Arial']

        ax1 = self.figure.add_subplot(221)
        ax1.set_facecolor('none')
        labels_barang = ['Tersedia', 'Dipinjam']
        sizes_barang = [summary['available_items'], summary['borrowed_items']]
        colors_barang = ['#00A896', '#FFA726']

        if sum(sizes_barang) == 0:
            ax1.text(0.5, 0.5, "Belum ada data", ha='center', va='center', fontweight='bold')
            ax1.axis('off')
        else:
            ax1.pie(sizes_barang, labels=labels_barang, colors=colors_barang, autopct='%1.1f%%', startangle=90, wedgeprops={'edgecolor': 'white', 'linewidth': 2})
            ax1.set_title('Proporsi Ketersediaan Aset', fontweight='bold', pad=10)

        ax2 = self.figure.add_subplot(222)
        ax2.set_facecolor('none')
        labels_transaksi = ['Aktif', 'Selesai']
        sizes_transaksi = [summary['active_loans'], summary['completed_loans']]
        colors_transaksi = ['#FFA726', '#E0E0E0']

        bars1 = ax2.bar(labels_transaksi, sizes_transaksi, color=colors_transaksi, width=0.5, zorder=3)
        ax2.set_title('Status Peminjaman', fontweight='bold', pad=10)
        ax2.grid(axis='y', linestyle='--', alpha=0.3, zorder=0)
        ax2.spines['top'].set_visible(False)
        ax2.spines['right'].set_visible(False)
        ax2.spines['left'].set_color('#CBD5E1')
        ax2.spines['bottom'].set_color('#CBD5E1')
        
        ax2.set_ylim(0, max(sizes_transaksi) + 2 if max(sizes_transaksi) > 0 else 5)
        ax2.yaxis.set_major_locator(matplotlib.ticker.MaxNLocator(integer=True))
        ax2.bar_label(bars1, padding=3, fontweight='bold')

        ax3 = self.figure.add_subplot(212)
        ax3.set_facecolor('none')
        kondisi_counts = {'Baik': 0, 'Rusak Ringan': 0, 'Rusak Berat': 0}
        for item in semua_barang:
            knd = item.get('condition', '')
            if knd in kondisi_counts:
                kondisi_counts[knd] += 1
                
        labels_kondisi = list(kondisi_counts.keys())
        sizes_kondisi = list(kondisi_counts.values())
        colors_kondisi = ['#00A896', '#FFB74D', '#E57373']
        
        bars2 = ax3.bar(labels_kondisi, sizes_kondisi, color=colors_kondisi, width=0.4, zorder=3)
        ax3.set_title('Rekapitulasi Kondisi Fisik Aset', fontweight='bold', pad=10)
        ax3.grid(axis='y', linestyle='--', alpha=0.3, zorder=0)
        ax3.spines['top'].set_visible(False)
        ax3.spines['right'].set_visible(False)
        ax3.spines['left'].set_color('#CBD5E1')
        ax3.spines['bottom'].set_color('#CBD5E1')
        
        ax3.set_ylim(0, max(sizes_kondisi) + 3 if max(sizes_kondisi) > 0 else 5)
        ax3.yaxis.set_major_locator(matplotlib.ticker.MaxNLocator(integer=True))
        ax3.bar_label(bars2, padding=3, fontweight='bold')

        self.figure.patch.set_facecolor('none')
        self.figure.tight_layout()
        self.canvas.draw()

    def create_items_page(self):
        page = QWidget()
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(12, 12, 12, 12)  # Layout spacing
        main_layout.setSpacing(15)

        # Left side: Item form
        left_widget = QFrame()
        left_widget.setObjectName("cardWidget")  # Connect QSS style
        left_widget.setMinimumWidth(280)
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(10, 10, 10, 10)
        left_layout.setSpacing(3)  # Tight spacing

        # Form header
        form_title = QLabel("Form Input Barang")
        form_title.setObjectName("formTitle")
        form_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #073B3A; margin-bottom: 5px;")
        left_layout.addWidget(form_title)

        # Form fields
        self.item_name_input = QLineEdit()
        self.item_name_input.setPlaceholderText("Masukkan nama barang")
        
        self.item_category_input = QLineEdit()
        self.item_category_input.setPlaceholderText("Akan ditebak AI otomatis...")
        
        self.item_quantity_input = QSpinBox()
        self.item_quantity_input.setMinimum(1)
        
        self.item_condition_input = QComboBox()
        self.item_condition_input.addItems(["Baik", "Rusak Ringan", "Rusak Berat"])
        
        self.item_location_input = QLineEdit()
        self.item_location_input.setPlaceholderText("Lokasi penyimpanan")
        
        self.item_description_input = QTextEdit()
        self.item_description_input.setFixedHeight(45)
        self.item_description_input.setPlaceholderText("Keterangan atau spesifikasi tambahan...")

        self.item_name_input.textChanged.connect(self.auto_predict_category)

        # Helper to add form labels
        def add_form_row(label_text, widget):
            lbl = QLabel(label_text)
            lbl.setObjectName("secondaryText")
            lbl.setStyleSheet("font-weight: 600; color: #557177; font-size: 11px;")
            left_layout.addWidget(lbl)
            left_layout.addWidget(widget)

        add_form_row("Nama Barang", self.item_name_input)
        add_form_row("Kategori", self.item_category_input)
        add_form_row("Jumlah", self.item_quantity_input)
        add_form_row("Kondisi", self.item_condition_input)
        add_form_row("Lokasi", self.item_location_input)
        add_form_row("Keterangan", self.item_description_input)

        # Spacing
        left_layout.addSpacing(4)

        # Action buttons row 1
        btn_row1 = QHBoxLayout()
        btn_row1.setSpacing(10)
        add_button = QPushButton("➕ Tambah")
        add_button.setObjectName("primaryBtn")  # Apply QSS style
        
        update_button = QPushButton("✏️ Perbarui")
        update_button.setObjectName("secondaryActionBtn")
        update_button.setStyleSheet("background-color: rgba(0, 122, 122, 0.1); color: #007A7A; font-weight: bold; border: none; border-radius: 10px; padding: 10px;")
        for button in (add_button, update_button):
            button.setMinimumHeight(30)
            button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        btn_row1.addWidget(add_button)
        btn_row1.addWidget(update_button)

        # Action buttons row 2
        btn_row2 = QHBoxLayout()
        btn_row2.setSpacing(10)
        delete_button = QPushButton("🗑️ Hapus")
        delete_button.setObjectName("btn_hapus_barang")  # Apply QSS style
        delete_button.setStyleSheet("background-color: #E57373; color: white; font-weight: bold; border: none; border-radius: 10px; padding: 10px;")
        
        reset_button = QPushButton("🔄 Bersihkan")
        reset_button.setObjectName("resetFormBtn")
        reset_button.setStyleSheet("background-color: #CFD8DC; color: #37474F; font-weight: bold; border: none; border-radius: 10px; padding: 10px;")
        for button in (delete_button, reset_button):
            button.setMinimumHeight(30)
            button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        btn_row2.addWidget(delete_button)
        btn_row2.addWidget(reset_button)

        # QR Code button
        generate_qr_button = QPushButton("🔲 Buat QR Code")
        generate_qr_button.setObjectName("btn_qr_barang")
        generate_qr_button.setStyleSheet("background-color: #455A64; color: white; font-weight: bold; border: none; border-radius: 10px; padding: 12px; margin-top: 5px;")
        generate_qr_button.setMinimumHeight(30)
        generate_qr_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        add_button.clicked.connect(self.add_item)
        update_button.clicked.connect(self.update_item)
        delete_button.clicked.connect(self.delete_item)
        reset_button.clicked.connect(self.clear_item_form)
        generate_qr_button.clicked.connect(self.generate_qr_code)

        left_layout.addLayout(btn_row1)
        left_layout.addLayout(btn_row2)
        left_layout.addWidget(generate_qr_button)

        left_widget.setLayout(left_layout)

        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)
        left_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        left_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        left_scroll.setFrameShape(QFrame.NoFrame)
        left_scroll.setMinimumWidth(300)
        left_scroll.setWidget(left_widget)

        # Right side: Search and table
        right_widget = QWidget()
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(15)

        # Search bar layout
        search_layout = QHBoxLayout()
        search_layout.setSpacing(10)
        
        self.item_search_input = QLineEdit()
        self.item_search_input.setPlaceholderText("Cari nama, kategori, kondisi, lokasi...")
        
        self.item_filter_status = QComboBox()
        self.item_filter_status.addItems(["Semua", "Tersedia", "Dipinjam"])
        self.item_filter_status.setFixedWidth(120)
        
        search_button = QPushButton("🔍 Cari")
        search_button.setObjectName("primaryBtn")
        search_button.setStyleSheet("padding: 8px 16px; font-weight: bold;")
        
        clear_search_button = QPushButton("Reset")
        clear_search_button.setObjectName("resetFormBtn")
        clear_search_button.setStyleSheet("background-color: #CFD8DC; color: #37474F; padding: 8px 16px; font-weight: bold; border: none; border-radius: 10px;")

        search_button.clicked.connect(self.load_items_table)
        clear_search_button.clicked.connect(self.reset_item_search)

        search_layout.addWidget(self.item_search_input)
        search_layout.addWidget(self.item_filter_status)
        search_layout.addWidget(search_button)
        search_layout.addWidget(clear_search_button)

        # Data table
        self.items_table = QTableWidget()
        self.items_table.setObjectName("mainTable")  # Apply QSS style
        self.items_table.setColumnCount(7)
        self.items_table.setHorizontalHeaderLabels([
            "ID", "Nama Barang", "Kategori", "Jumlah", "Kondisi", "Lokasi", "Status"
        ])
        self.items_table.setSelectionBehavior(QTableWidget.SelectRows)
        
        # Configure table focus and grid
        self.items_table.setFocusPolicy(Qt.NoFocus)
        self.items_table.setShowGrid(False)
        
        # Table structure
        self.items_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.items_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.items_table.horizontalHeader().setMinimumSectionSize(95)
        self.items_table.verticalHeader().setVisible(False)  # Hide vertical header
        self.items_table.setAlternatingRowColors(True)       # Enable alternating row colors
        self.items_table.cellClicked.connect(self.load_item_form)

        right_layout.addLayout(search_layout)
        right_layout.addWidget(self.items_table)
        right_widget.setLayout(right_layout)

        # Apply drop shadow
        shadow_left = QGraphicsDropShadowEffect(left_widget)
        shadow_left.setBlurRadius(30)
        shadow_left.setXOffset(0)
        shadow_left.setYOffset(10)
        shadow_left.setColor(QColor(0, 80, 80, 12))  # Set shadow color
        left_widget.setGraphicsEffect(shadow_left)

        shadow_table = QGraphicsDropShadowEffect(self.items_table)
        shadow_table.setBlurRadius(25)
        shadow_table.setXOffset(0)
        shadow_table.setYOffset(8)
        shadow_table.setColor(QColor(0, 80, 80, 8))
        self.items_table.setGraphicsEffect(shadow_table)

        main_layout.addWidget(left_scroll, 1)
        main_layout.addWidget(right_widget, 2)

        page.setLayout(main_layout)
        return page

    def create_loans_page(self):
        page = QWidget()
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(12, 12, 12, 12)  # Layout spacing
        main_layout.setSpacing(15)

        # Left side: Loan form
        left_widget = QFrame()
        left_widget.setObjectName("cardWidget")  # Connect QSS style
        left_widget.setMinimumWidth(280)
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(10, 10, 10, 10)
        left_layout.setSpacing(3)  # Tight spacing

        # Form header
        form_title = QLabel("Form Peminjaman")
        form_title.setObjectName("formTitle")
        form_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #073B3A; margin-bottom: 5px;")
        left_layout.addWidget(form_title)

        # Form fields
        self.loan_item_id_input = QLineEdit()
        self.loan_item_id_input.setReadOnly(True)
        self.loan_item_id_input.setPlaceholderText("ID Otomatis...")
        
        # Select item layout with browse button
        selector_container = QWidget()
        selector_layout = QHBoxLayout(selector_container)
        selector_layout.setContentsMargins(0, 0, 0, 0)
        selector_layout.setSpacing(5)
        
        self.loan_item_selector = QComboBox()
        self.loan_item_selector.setMinimumHeight(30)
        self.loan_item_selector.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.loan_item_selector.setEditable(True)
        self.loan_item_selector.setInsertPolicy(QComboBox.NoInsert)
        self.loan_item_selector.lineEdit().setPlaceholderText("Ketik/pilih nama barang...")
        self.loan_item_selector.currentIndexChanged.connect(self.on_loan_item_changed)
        
        # Enable autocomplete filter mode
        completer = self.loan_item_selector.completer()
        if completer:
            completer.setFilterMode(Qt.MatchContains)
            completer.setCompletionMode(QCompleter.PopupCompletion)
            
        self.btn_browse_item = QPushButton("🔍")
        self.btn_browse_item.setFixedWidth(36)
        self.btn_browse_item.setMinimumHeight(30)
        self.btn_browse_item.setMaximumHeight(30)
        self.btn_browse_item.setObjectName("primaryBtn")
        self.btn_browse_item.setToolTip("Cari barang dari katalog")
        self.btn_browse_item.setStyleSheet("padding: 0; font-size: 14px;")
        self.btn_browse_item.clicked.connect(self.browse_items_dialog)
        
        selector_layout.addWidget(self.loan_item_selector)
        selector_layout.addWidget(self.btn_browse_item)
        self.borrower_name_input = QLineEdit()
        self.borrower_name_input.setPlaceholderText("Masukkan nama peminjam")
        
        self.borrower_id_input = QLineEdit()
        self.borrower_id_input.setPlaceholderText("Masukkan NIM atau ID")

        self.loan_quantity_input = QSpinBox()
        self.loan_quantity_input.setMinimum(1)
        self.loan_quantity_input.setMinimumHeight(30)
        self.loan_quantity_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        self.borrow_date_input = QDateEdit(QDate.currentDate())
        self.borrow_date_input.setCalendarPopup(True)
        self.return_date_input = QDateEdit(QDate.currentDate())
        self.return_date_input.setCalendarPopup(True)
        for date_input in (self.borrow_date_input, self.return_date_input):
            date_input.setMinimumWidth(90)
            date_input.setMinimumHeight(30)
            date_input.setMaximumHeight(30)
            date_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        self.loan_status_input = QComboBox()
        self.loan_status_input.addItems(["Dipinjam", "Selesai"])
        self.loan_status_input.setMinimumHeight(30)
        self.loan_status_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        self.loan_notes_input = QTextEdit()
        self.loan_notes_input.setFixedHeight(45)
        self.loan_notes_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.loan_notes_input.setPlaceholderText("Catatan tambahan jika ada...")

        # Helper to add form labels
        def create_labeled_widget(label_text, widget):
            lbl = QLabel(label_text)
            lbl.setObjectName("secondaryText")
            lbl.setStyleSheet("font-weight: 600; color: #557177; font-size: 11px;")
            left_layout.addWidget(lbl)
            left_layout.addWidget(widget)

        create_labeled_widget("ID Barang (Otomatis)", self.loan_item_id_input)
        create_labeled_widget("Pilih Nama Barang", selector_container)
        create_labeled_widget("Nama Peminjam", self.borrower_name_input)
        create_labeled_widget("NIM / ID Peminjam", self.borrower_id_input)
        create_labeled_widget("Jumlah Pinjam", self.loan_quantity_input)
        
        # Date fields layout
        date_layout = QHBoxLayout()
        date_box1 = QVBoxLayout()
        lbl_tgl_pinjam = QLabel("Tgl Pinjam")
        lbl_tgl_pinjam.setStyleSheet("font-weight: 600; color: #557177; font-size: 11px;")
        date_box1.addWidget(lbl_tgl_pinjam)
        date_box1.addWidget(self.borrow_date_input)
        
        date_box2 = QVBoxLayout()
        lbl_tgl_kembali = QLabel("Tgl Kembali")
        lbl_tgl_kembali.setStyleSheet("font-weight: 600; color: #557177; font-size: 11px;")
        date_box2.addWidget(lbl_tgl_kembali)
        date_box2.addWidget(self.return_date_input)
        
        date_layout.addLayout(date_box1)
        date_layout.addLayout(date_box2)
        left_layout.addLayout(date_layout)

        create_labeled_widget("Status Peminjaman", self.loan_status_input)
        create_labeled_widget("Catatan", self.loan_notes_input)

        # Action buttons
        left_layout.addSpacing(4)
        
        btn_row1 = QHBoxLayout()
        btn_row1.setSpacing(10)
        add_loan_button = QPushButton("➕ Tambah")
        add_loan_button.setObjectName("primaryBtn")  # Apply QSS style
        
        update_loan_button = QPushButton("✏️ Perbarui")
        update_loan_button.setObjectName("secondaryActionBtn") # Apply QSS style
        update_loan_button.setStyleSheet("background-color: rgba(0, 122, 122, 0.1); color: #007A7A; font-weight: bold; border: none; border-radius: 10px; padding: 10px;")
        for button in (add_loan_button, update_loan_button):
            button.setMinimumHeight(30)
            button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        btn_row1.addWidget(add_loan_button)
        btn_row1.addWidget(update_loan_button)

        btn_row2 = QHBoxLayout()
        btn_row2.setSpacing(10)
        mark_return_button = QPushButton("✅ Tandai Selesai")
        mark_return_button.setObjectName("successBtn") # Apply QSS style
        mark_return_button.setStyleSheet("background-color: #26A69A; color: white; font-weight: bold; border: none; border-radius: 10px; padding: 10px;")
        
        reset_loan_form_button = QPushButton("🔄 Bersihkan")
        reset_loan_form_button.setObjectName("resetFormBtn") # Apply QSS style
        reset_loan_form_button.setStyleSheet("background-color: #CFD8DC; color: #37474F; font-weight: bold; border: none; border-radius: 10px; padding: 10px;")
        for button in (mark_return_button, reset_loan_form_button):
            button.setMinimumHeight(30)
            button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        btn_row2.addWidget(mark_return_button)
        btn_row2.addWidget(reset_loan_form_button)

        add_loan_button.clicked.connect(self.add_loan)
        update_loan_button.clicked.connect(self.update_loan)
        mark_return_button.clicked.connect(self.mark_returned)
        reset_loan_form_button.clicked.connect(self.clear_loan_form)

        left_layout.addLayout(btn_row1)
        left_layout.addLayout(btn_row2)

        left_widget.setLayout(left_layout)

        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)
        left_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        left_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        left_scroll.setFrameShape(QFrame.NoFrame)
        left_scroll.setMinimumWidth(300)
        left_scroll.setWidget(left_widget)

        # Right side: Tabbed table container
        right_widget = QWidget()
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(15)

        # Tab Widget
        self.loans_tab_widget = QTabWidget()
        self.loans_tab_widget.setObjectName("loansTabWidget")

        # Tab 1: Transaksi Peminjaman
        tab_loans = QWidget()
        tab_loans_layout = QVBoxLayout(tab_loans)
        tab_loans_layout.setContentsMargins(12, 12, 12, 12)
        tab_loans_layout.setSpacing(12)

        # Tab 1 Search bar layout
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(10)
        
        self.loan_search_input = QLineEdit()
        self.loan_search_input.setPlaceholderText("Cari nama peminjam, barang, status...")
        self.loan_search_input.setMinimumHeight(36)
        
        self.loan_filter_status = QComboBox()
        self.loan_filter_status.addItems(["Semua", "Dipinjam", "Selesai"])
        self.loan_filter_status.setFixedWidth(120)
        self.loan_filter_status.setMinimumHeight(36)
        
        loan_search_button = QPushButton("🔍 Cari")
        loan_search_button.setObjectName("primaryBtn")
        loan_search_button.setStyleSheet("padding: 8px 16px; font-weight: bold;")
        
        loan_reset_button = QPushButton("Reset")
        loan_reset_button.setObjectName("resetFormBtn")
        loan_reset_button.setStyleSheet("background-color: #CFD8DC; color: #37474F; padding: 8px 16px; font-weight: bold; border: none; border-radius: 10px;")

        loan_search_button.clicked.connect(self.load_loans_table)
        loan_reset_button.clicked.connect(self.reset_loan_search)

        filter_layout.addWidget(self.loan_search_input)
        filter_layout.addWidget(self.loan_filter_status)
        filter_layout.addWidget(loan_search_button)
        filter_layout.addWidget(loan_reset_button)

        # Tab 1 Data table
        self.loans_table = QTableWidget()
        self.loans_table.setObjectName("mainTable") # Apply QSS style
        self.loans_table.setColumnCount(8)
        self.loans_table.setHorizontalHeaderLabels([
            "ID", "Nama Barang", "Nama Peminjam", "NIM/ID", 
            "Jumlah", "Tgl Pinjam", "Tgl Kembali", "Status"
        ])
        self.loans_table.setSelectionBehavior(QTableWidget.SelectRows)
        
        # Configure table focus and grid
        self.loans_table.setFocusPolicy(Qt.NoFocus)
        self.loans_table.setShowGrid(False)
        
        # Table structure
        self.loans_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.loans_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.loans_table.horizontalHeader().setMinimumSectionSize(100)
        self.loans_table.verticalHeader().setVisible(False) # Hide vertical header
        self.loans_table.setAlternatingRowColors(True) # Enable alternating row colors
        self.loans_table.cellClicked.connect(self.load_loan_form)

        tab_loans_layout.addLayout(filter_layout)
        tab_loans_layout.addWidget(self.loans_table)

        # Tab 2: Katalog Barang Tersedia
        tab_catalog = QWidget()
        tab_catalog_layout = QVBoxLayout(tab_catalog)
        tab_catalog_layout.setContentsMargins(12, 12, 12, 12)
        tab_catalog_layout.setSpacing(12)

        # Tab 2 Search bar layout
        catalog_filter_layout = QHBoxLayout()
        catalog_filter_layout.setSpacing(10)

        self.loan_catalog_search_input = QLineEdit()
        self.loan_catalog_search_input.setPlaceholderText("Cari barang (nama, kategori, lokasi, kondisi)...")
        self.loan_catalog_search_input.setMinimumHeight(36)
        self.loan_catalog_search_input.textChanged.connect(self.load_loan_catalog_table)

        btn_refresh_catalog = QPushButton("🔄 Refresh")
        btn_refresh_catalog.setMinimumHeight(36)
        btn_refresh_catalog.setObjectName("primaryBtn")
        btn_refresh_catalog.setStyleSheet("padding: 8px 16px; font-weight: bold;")
        btn_refresh_catalog.clicked.connect(self.load_loan_catalog_table)

        catalog_filter_layout.addWidget(self.loan_catalog_search_input)
        catalog_filter_layout.addWidget(btn_refresh_catalog)

        # Tab 2 Data table
        self.loan_catalog_table = QTableWidget()
        self.loan_catalog_table.setObjectName("mainTable")
        self.loan_catalog_table.setColumnCount(6)
        self.loan_catalog_table.setHorizontalHeaderLabels([
            "ID", "Nama Barang", "Kategori", "Stok Tersedia", "Kondisi", "Lokasi"
        ])
        self.loan_catalog_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.loan_catalog_table.setSelectionMode(QTableWidget.SingleSelection)
        self.loan_catalog_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.loan_catalog_table.setFocusPolicy(Qt.NoFocus)
        self.loan_catalog_table.setShowGrid(False)
        self.loan_catalog_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.loan_catalog_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.loan_catalog_table.horizontalHeader().setMinimumSectionSize(95)
        self.loan_catalog_table.verticalHeader().setVisible(False)
        self.loan_catalog_table.setAlternatingRowColors(True)
        self.loan_catalog_table.cellDoubleClicked.connect(self.select_item_from_catalog_table)

        tab_catalog_layout.addLayout(catalog_filter_layout)
        tab_catalog_layout.addWidget(self.loan_catalog_table)

        # Add tabs to QTabWidget
        self.loans_tab_widget.addTab(tab_loans, "📋 Transaksi Peminjaman")
        self.loans_tab_widget.addTab(tab_catalog, "📦 Katalog Barang Tersedia")

        right_layout.addWidget(self.loans_tab_widget)
        right_widget.setLayout(right_layout)

        # Apply drop shadow
        shadow_left = QGraphicsDropShadowEffect(left_widget)
        shadow_left.setBlurRadius(30)
        shadow_left.setXOffset(0)
        shadow_left.setYOffset(10)
        shadow_left.setColor(QColor(0, 80, 80, 12))  # Set shadow color
        left_widget.setGraphicsEffect(shadow_left)

        shadow_tab = QGraphicsDropShadowEffect(self.loans_tab_widget)
        shadow_tab.setBlurRadius(25)
        shadow_tab.setXOffset(0)
        shadow_tab.setYOffset(8)
        shadow_tab.setColor(QColor(0, 80, 80, 8))
        self.loans_tab_widget.setGraphicsEffect(shadow_tab)

        main_layout.addWidget(left_scroll, 1)
        main_layout.addWidget(right_widget, 2)

        page.setLayout(main_layout)
        return page

    def auto_predict_category(self, text):
        kategori = self.ai.predict_category(text)
        self.item_category_input.setText(kategori)

    def populate_loan_item_fields(self, item_id, item_name):
        self.loan_item_id_input.setText(str(item_id))
        index = self.loan_item_selector.findData(item_id)
        if index >= 0:
            self.loan_item_selector.setCurrentIndex(index)

    def on_loan_item_changed(self, index):
        if index >= 0:
            item_id = self.loan_item_selector.itemData(index)
            self.loan_item_id_input.setText(str(item_id))
            
            item = self.db_manager.get_item_by_id(item_id)
            if item:
                # Batasi jumlah maksimal peminjaman sesuai stok
                self.loan_quantity_input.setMaximum(max(1, item['quantity']))
        else:
            self.loan_item_id_input.clear()

    def browse_items_dialog(self):
        # Alih-alih membuka popup dialog baru, kita langsung alihkan tab kanan ke Katalog Barang Tersedia
        self.loans_tab_widget.setCurrentIndex(1)
        self.loan_catalog_search_input.setFocus()

    def load_loan_catalog_table(self):
        query = self.loan_catalog_search_input.text().strip()
        items = self.db_manager.search_items(query, "Semua")
        
        # Saring hanya barang yang stoknya lebih dari nol
        filtered_items = [item for item in items if item["quantity"] > 0]
        
        self.loan_catalog_table.setRowCount(len(filtered_items))
        for row_index, item in enumerate(filtered_items):
            self.loan_catalog_table.setItem(row_index, 0, QTableWidgetItem(str(item["id"])))
            self.loan_catalog_table.setItem(row_index, 1, QTableWidgetItem(item["name"]))
            self.loan_catalog_table.setItem(row_index, 2, QTableWidgetItem(item["category"]))
            self.loan_catalog_table.setItem(row_index, 3, QTableWidgetItem(str(item["quantity"])))
            self.loan_catalog_table.setItem(row_index, 4, QTableWidgetItem(item["condition"]))
            self.loan_catalog_table.setItem(row_index, 5, QTableWidgetItem(item["location"]))

    def select_item_from_catalog_table(self, row, _column):
        item_id_str = self.loan_catalog_table.item(row, 0).text()
        item_id = int(item_id_str)
        
        # Temukan dan pilih barang pada dropdown di form kiri
        index = self.loan_item_selector.findData(item_id)
        if index >= 0:
            self.loan_item_selector.setCurrentIndex(index)
            # Pindahkan kembali tab kanan ke daftar transaksi peminjaman
            self.loans_tab_widget.setCurrentIndex(0)
            # Fokuskan input nama peminjam agar user tinggal mengetik nama
            self.borrower_name_input.setFocus()

    def refresh_loan_item_selector(self):
        self.loan_item_selector.blockSignals(True)
        self.loan_item_selector.clear()
        
        # Load all items from DB
        items = self.db_manager.get_items()
        for item in items:
            self.loan_item_selector.addItem(f"{item['name']} (Stok: {item['quantity']})", item["id"])
            
        self.loan_item_selector.setCurrentIndex(-1)
        if self.loan_item_selector.lineEdit():
            self.loan_item_selector.lineEdit().clear()
        self.loan_item_id_input.clear()
        self.loan_item_selector.blockSignals(False)

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
        self.populate_loan_item_fields(item["id"], item["name"])

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

        new_item_id = self.db_manager.add_item(name, category, quantity, condition, location, description)
        self.load_items_table()
        self.load_dashboard()
        QMessageBox.information(self, "Sukses", "Barang berhasil ditambahkan.")
        self.clear_item_form()
        self.populate_loan_item_fields(new_item_id, name)

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
        
        # Select in combobox
        index = self.loan_item_selector.findData(loan["item_id"])
        if index >= 0:
            self.loan_item_selector.setCurrentIndex(index)
        else:
            self.loan_item_selector.addItem(f"{loan['item_name']} (Item Terhapus)", loan["item_id"])
            self.loan_item_selector.setCurrentIndex(self.loan_item_selector.count() - 1)
            
        self.borrower_name_input.setText(loan["borrower_name"])
        self.borrower_id_input.setText(loan["borrower_id"])
        self.loan_quantity_input.setValue(loan["quantity"])
        self.borrow_date_input.setDate(QDate.fromString(loan["borrow_date"], "yyyy-MM-dd"))
        self.return_date_input.setDate(QDate.fromString(loan["return_date"], "yyyy-MM-dd"))
        index_status = self.loan_status_input.findText(loan["status"])
        self.loan_status_input.setCurrentIndex(index_status if index_status >= 0 else 0)
        self.loan_notes_input.setPlainText(loan["notes"] or "")

    def clear_loan_form(self):
        self.current_loan_id = None
        self.loan_item_id_input.clear()
        self.loan_item_selector.setCurrentIndex(-1)
        if self.loan_item_selector.lineEdit():
            self.loan_item_selector.lineEdit().clear()
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
            QMessageBox.warning(self, "Validasi", "Pilih barang dari tabel terlebih dahulu.")
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
        self.load_loan_catalog_table()
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
        self.load_loan_catalog_table()
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
        self.load_loan_catalog_table()
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
                self.load_loan_catalog_table()
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

    def show_dashboard_page(self):
        self.load_dashboard()
        self.stack.setCurrentWidget(self.dashboard_page)

    def show_items_page(self):
        self.load_items_table()
        self.stack.setCurrentWidget(self.items_page)

    def show_loans_page(self):
        self.load_loans_table()
        self.load_loan_catalog_table()
        self.refresh_loan_item_selector()
        if hasattr(self, 'loan_catalog_search_input'):
            self.loan_catalog_search_input.clear()
        if hasattr(self, 'loans_tab_widget'):
            self.loans_tab_widget.setCurrentIndex(1)
        self.stack.setCurrentWidget(self.loans_page)


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
