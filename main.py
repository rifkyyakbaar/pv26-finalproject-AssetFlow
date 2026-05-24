import os
import sys
import hashlib
from datetime import datetime

from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QIcon
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

from database.db import DatabaseManager
from utils.exporter import export_csv, export_pdf

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "assetflow.db")
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
        self.setWindowTitle("AssetFlow - Aplikasi Manajemen Aset")
        self.resize(1200, 760)
        self.current_item_id = None
        self.current_loan_id = None
        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        main_layout = QHBoxLayout()

        self.sidebar = self.create_sidebar()
        self.stack = QStackedWidget()

        self.dashboard_page = self.create_dashboard_page()
        self.items_page = self.create_items_page()
        self.loans_page = self.create_loans_page()

        self.stack.addWidget(self.dashboard_page)
        self.stack.addWidget(self.items_page)
        self.stack.addWidget(self.loans_page)

        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(self.stack, 1)
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        self.load_dashboard()
        self.load_items_table()
        self.load_loans_table()

    def create_sidebar(self):
        sidebar = QGroupBox("Menu Navigasi")
        sidebar.setFixedWidth(220)
        layout = QVBoxLayout()

        btn_dashboard = QPushButton("Dashboard")
        btn_items = QPushButton("Master Barang")
        btn_loans = QPushButton("Data Peminjaman")
        btn_logout = QPushButton("Logout")

        btn_dashboard.clicked.connect(lambda: self.stack.setCurrentWidget(self.dashboard_page))
        btn_items.clicked.connect(lambda: self.stack.setCurrentWidget(self.items_page))
        btn_loans.clicked.connect(lambda: self.stack.setCurrentWidget(self.loans_page))
        btn_logout.clicked.connect(self.logout)

        layout.addWidget(btn_dashboard)
        layout.addWidget(btn_items)
        layout.addWidget(btn_loans)
        layout.addStretch()
        layout.addWidget(btn_logout)

        sidebar.setLayout(layout)
        return sidebar

    def create_dashboard_page(self):
        page = QWidget()
        layout = QVBoxLayout()

        self.summary_label = QLabel()
        self.summary_label.setWordWrap(True)

        export_items_btn = QPushButton("Export Master Barang CSV")
        export_loans_btn = QPushButton("Export Peminjaman CSV")
        export_items_pdf_btn = QPushButton("Export Master Barang PDF")
        export_loans_pdf_btn = QPushButton("Export Peminjaman PDF")

        export_items_btn.clicked.connect(self.export_items_csv)
        export_loans_btn.clicked.connect(self.export_loans_csv)
        export_items_pdf_btn.clicked.connect(self.export_items_pdf)
        export_loans_pdf_btn.clicked.connect(self.export_loans_pdf)

        layout.addWidget(QLabel("Dashboard Ringkasan"))
        layout.addWidget(self.summary_label)
        layout.addWidget(export_items_btn)
        layout.addWidget(export_loans_btn)
        layout.addWidget(export_items_pdf_btn)
        layout.addWidget(export_loans_pdf_btn)
        layout.addStretch()
        page.setLayout(layout)
        return page

    def create_items_page(self):
        page = QWidget()
        layout = QVBoxLayout()

        search_layout = QHBoxLayout()
        self.item_search_input = QLineEdit()
        self.item_search_input.setPlaceholderText("Cari nama, kategori, kondisi, lokasi...")
        self.item_filter_status = QComboBox()
        self.item_filter_status.addItems(["Semua", "Tersedia", "Dipinjam"])
        search_button = QPushButton("Cari")
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
            "ID",
            "Nama Barang",
            "Kategori",
            "Jumlah",
            "Kondisi",
            "Lokasi",
            "Status",
        ])
        self.items_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.items_table.cellClicked.connect(self.load_item_form)

        form_layout = QVBoxLayout()
        self.item_name_input = QLineEdit()
        self.item_category_input = QLineEdit()
        self.item_quantity_input = QSpinBox()
        self.item_quantity_input.setMinimum(1)
        self.item_condition_input = QComboBox()
        self.item_condition_input.addItems(["Baik", "Rusak Ringan", "Rusak Berat"])
        self.item_location_input = QLineEdit()
        self.item_description_input = QTextEdit()
        self.item_description_input.setFixedHeight(70)

        form_layout.addWidget(QLabel("Nama Barang"))
        form_layout.addWidget(self.item_name_input)
        form_layout.addWidget(QLabel("Kategori"))
        form_layout.addWidget(self.item_category_input)
        form_layout.addWidget(QLabel("Jumlah"))
        form_layout.addWidget(self.item_quantity_input)
        form_layout.addWidget(QLabel("Kondisi"))
        form_layout.addWidget(self.item_condition_input)
        form_layout.addWidget(QLabel("Lokasi"))
        form_layout.addWidget(self.item_location_input)
        form_layout.addWidget(QLabel("Keterangan"))
        form_layout.addWidget(self.item_description_input)

        buttons_layout = QHBoxLayout()
        add_button = QPushButton("Tambah Barang")
        update_button = QPushButton("Perbarui Barang")
        delete_button = QPushButton("Hapus Barang")
        reset_button = QPushButton("Bersihkan Form")

        add_button.clicked.connect(self.add_item)
        update_button.clicked.connect(self.update_item)
        delete_button.clicked.connect(self.delete_item)
        reset_button.clicked.connect(self.clear_item_form)

        buttons_layout.addWidget(add_button)
        buttons_layout.addWidget(update_button)
        buttons_layout.addWidget(delete_button)
        buttons_layout.addWidget(reset_button)

        layout.addLayout(search_layout)
        layout.addWidget(self.items_table)
        layout.addLayout(form_layout)
        layout.addLayout(buttons_layout)
        page.setLayout(layout)
        return page

    def create_loans_page(self):
        page = QWidget()
        layout = QVBoxLayout()

        filter_layout = QHBoxLayout()
        self.loan_search_input = QLineEdit()
        self.loan_search_input.setPlaceholderText("Cari nama peminjam, barang, status...")
        self.loan_filter_status = QComboBox()
        self.loan_filter_status.addItems(["Semua", "Dipinjam", "Selesai"])
        loan_search_button = QPushButton("Cari")
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
            "ID",
            "Nama Barang",
            "Nama Peminjam",
            "NIM/ID",
            "Jumlah",
            "Tanggal Pinjam",
            "Tanggal Kembali",
            "Status",
        ])
        self.loans_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.loans_table.cellClicked.connect(self.load_loan_form)

        form_layout = QVBoxLayout()
        self.loan_item_input = QLineEdit()
        self.loan_item_input.setReadOnly(True)
        self.loan_item_id_input = QLineEdit()
        self.loan_item_id_input.setReadOnly(True)
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
        self.loan_notes_input.setFixedHeight(70)

        form_layout.addWidget(QLabel("ID Barang"))
        form_layout.addWidget(self.loan_item_id_input)
        form_layout.addWidget(QLabel("Nama Barang"))
        form_layout.addWidget(self.loan_item_input)
        form_layout.addWidget(QLabel("Nama Peminjam"))
        form_layout.addWidget(self.borrower_name_input)
        form_layout.addWidget(QLabel("NIM / ID Peminjam"))
        form_layout.addWidget(self.borrower_id_input)
        form_layout.addWidget(QLabel("Jumlah Peminjaman"))
        form_layout.addWidget(self.loan_quantity_input)
        form_layout.addWidget(QLabel("Tanggal Pinjam"))
        form_layout.addWidget(self.borrow_date_input)
        form_layout.addWidget(QLabel("Tanggal Kembali"))
        form_layout.addWidget(self.return_date_input)
        form_layout.addWidget(QLabel("Status Peminjaman"))
        form_layout.addWidget(self.loan_status_input)
        form_layout.addWidget(QLabel("Catatan"))
        form_layout.addWidget(self.loan_notes_input)

        buttons_layout = QHBoxLayout()
        add_loan_button = QPushButton("Tambah Peminjaman")
        update_loan_button = QPushButton("Perbarui Peminjaman")
        mark_return_button = QPushButton("Tandai Selesai")
        reset_loan_form_button = QPushButton("Bersihkan Form")

        add_loan_button.clicked.connect(self.add_loan)
        update_loan_button.clicked.connect(self.update_loan)
        mark_return_button.clicked.connect(self.mark_returned)
        reset_loan_form_button.clicked.connect(self.clear_loan_form)

        buttons_layout.addWidget(add_loan_button)
        buttons_layout.addWidget(update_loan_button)
        buttons_layout.addWidget(mark_return_button)
        buttons_layout.addWidget(reset_loan_form_button)

        layout.addLayout(filter_layout)
        layout.addWidget(self.loans_table)
        layout.addLayout(form_layout)
        layout.addLayout(buttons_layout)
        page.setLayout(layout)
        return page

    def logout(self):
        self.close()

    def load_dashboard(self):
        summary = self.db_manager.get_dashboard_summary()
        message = (
            f"Total Barang: {summary['total_items']}\n"
            f"Barang Tersedia: {summary['available_items']}\n"
            f"Barang Dipinjam: {summary['borrowed_items']}\n"
            f"Total Transaksi Peminjaman: {summary['total_loans']}\n"
            f"Transaksi Aktif: {summary['active_loans']}\n"
            f"Transaksi Selesai: {summary['completed_loans']}"
        )
        self.summary_label.setText(message)

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
        self.item_name_input.setText(item["name"])
        self.item_category_input.setText(item["category"])
        self.item_quantity_input.setValue(item["quantity"])
        index = self.item_condition_input.findText(item["condition"])
        self.item_condition_input.setCurrentIndex(index if index >= 0 else 0)
        self.item_location_input.setText(item["location"])
        self.item_description_input.setPlainText(item["description"])

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
            QMessageBox.warning(self, "Validasi", "Pilih barang dari tabel item terlebih dahulu.")
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
