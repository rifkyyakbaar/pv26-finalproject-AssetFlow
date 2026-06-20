import sqlite3
import hashlib
from datetime import datetime


class DatabaseManager:
    def __init__(self, db_path):
        self.db_path = db_path
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        self.create_schema()

    def create_schema(self):
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
            """
        )
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                condition TEXT NOT NULL,
                location TEXT NOT NULL,
                description TEXT,
                status TEXT NOT NULL DEFAULT 'Tersedia',
                created_at TEXT NOT NULL
            )
            """
        )
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS loans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER NOT NULL,
                borrower_name TEXT NOT NULL,
                borrower_id TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                borrow_date TEXT NOT NULL,
                return_date TEXT NOT NULL,
                status TEXT NOT NULL,
                notes TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY(item_id) REFERENCES items(id) ON DELETE CASCADE
            )
            """
        )
        self.connection.commit()
        self.ensure_default_admin()

    def ensure_default_admin(self):
        cursor = self.connection.cursor()
        cursor.execute("SELECT id FROM users WHERE username = ?", ("admin",))
        if cursor.fetchone() is None:
            password_hash = self.hash_password("admin123")
            cursor.execute("INSERT INTO users(username, password) VALUES(?, ?)", ("admin", password_hash))
            self.connection.commit()

    @staticmethod
    def hash_password(password):
        return hashlib.sha256(password.encode("utf-8")).hexdigest()

    def authenticate_user(self, username, password):
        cursor = self.connection.cursor()
        cursor.execute("SELECT password FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        if row is None:
            return False
        return row["password"] == self.hash_password(password)

    def add_item(self, name, category, quantity, condition, location, description):
        status = "Tersedia"
        created_at = datetime.now().isoformat()
        cursor = self.connection.execute(
            "INSERT INTO items(name, category, quantity, condition, location, description, status, created_at) VALUES(?, ?, ?, ?, ?, ?, ?, ?)",
            (name, category, quantity, condition, location, description, status, created_at),
        )
        self.connection.commit()
        return cursor.lastrowid

    def update_item(self, item_id, name, category, quantity, condition, location, description):
        status = "Tersedia" if quantity > 0 else "Dipinjam"
        self.connection.execute(
            "UPDATE items SET name = ?, category = ?, quantity = ?, condition = ?, location = ?, description = ?, status = ? WHERE id = ?",
            (name, category, quantity, condition, location, description, status, item_id),
        )
        self.connection.commit()

    def delete_item(self, item_id):
        self.connection.execute("DELETE FROM items WHERE id = ?", (item_id,))
        self.connection.commit()

    def get_item_by_id(self, item_id):
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM items WHERE id = ?", (item_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_items(self):
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM items ORDER BY id DESC")
        return [dict(row) for row in cursor.fetchall()]

    def search_items(self, query, status_filter):
        cursor = self.connection.cursor()
        sql = "SELECT * FROM items"
        conditions = []
        params = []

        if query:
            conditions.append("(name LIKE ? OR category LIKE ? OR condition LIKE ? OR location LIKE ?)")
            wildcard = f"%{query}%"
            params.extend([wildcard, wildcard, wildcard, wildcard])

        if status_filter and status_filter != "Semua":
            conditions.append("status = ?")
            params.append(status_filter)

        if conditions:
            sql += " WHERE " + " AND ".join(conditions)

        sql += " ORDER BY id DESC"
        cursor.execute(sql, params)
        return [dict(row) for row in cursor.fetchall()]

    def add_loan(self, item_id, borrower_name, borrower_id, quantity, borrow_date, return_date, status, notes):
        item = self.get_item_by_id(item_id)
        if item is None:
            return False, "Barang tidak ditemukan."
        if quantity <= 0:
            return False, "Jumlah peminjaman harus lebih besar dari nol."
        if quantity > item["quantity"]:
            return False, "Jumlah peminjaman melebihi stok yang tersedia."

        created_at = datetime.now().isoformat()
        self.connection.execute(
            "INSERT INTO loans(item_id, borrower_name, borrower_id, quantity, borrow_date, return_date, status, notes, created_at) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (item_id, borrower_name, borrower_id, quantity, borrow_date, return_date, status, notes, created_at),
        )

        new_quantity = item["quantity"] - quantity
        new_status = "Dipinjam" if new_quantity < item["quantity"] else item["status"]
        self.connection.execute(
            "UPDATE items SET quantity = ?, status = ? WHERE id = ?",
            (new_quantity, new_status, item_id),
        )
        self.connection.commit()
        return True, "OK"

    def get_loan_by_id(self, loan_id):
        cursor = self.connection.cursor()
        cursor.execute(
            "SELECT loans.*, items.name as item_name FROM loans JOIN items ON loans.item_id = items.id WHERE loans.id = ?",
            (loan_id,),
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_loans(self):
        cursor = self.connection.cursor()
        cursor.execute(
            "SELECT loans.id, loans.item_id, items.name as item_name, loans.borrower_name, loans.borrower_id, loans.quantity, loans.borrow_date, loans.return_date, loans.status, loans.notes FROM loans JOIN items ON loans.item_id = items.id ORDER BY loans.id DESC"
        )
        return [dict(row) for row in cursor.fetchall()]

    def search_loans(self, query, status_filter):
        cursor = self.connection.cursor()
        sql = "SELECT loans.id, loans.item_id, items.name as item_name, loans.borrower_name, loans.borrower_id, loans.quantity, loans.borrow_date, loans.return_date, loans.status, loans.notes FROM loans JOIN items ON loans.item_id = items.id"
        conditions = []
        params = []

        if query:
            conditions.append("(items.name LIKE ? OR loans.borrower_name LIKE ? OR loans.borrower_id LIKE ? OR loans.status LIKE ?)")
            wildcard = f"%{query}%"
            params.extend([wildcard, wildcard, wildcard, wildcard])

        if status_filter and status_filter != "Semua":
            conditions.append("loans.status = ?")
            params.append(status_filter)

        if conditions:
            sql += " WHERE " + " AND ".join(conditions)

        sql += " ORDER BY loans.id DESC"
        cursor.execute(sql, params)
        return [dict(row) for row in cursor.fetchall()]

    def update_loan(self, loan_id, borrower_name, borrower_id, quantity, borrow_date, return_date, status, notes):
        loan = self.get_loan_by_id(loan_id)
        if loan is None:
            return False

        item = self.get_item_by_id(loan["item_id"])
        if item is None:
            return False

        current_quantity = item["quantity"] + loan["quantity"]
        if quantity > current_quantity:
            return False

        new_item_quantity = current_quantity - quantity
        self.connection.execute(
            "UPDATE loans SET borrower_name = ?, borrower_id = ?, quantity = ?, borrow_date = ?, return_date = ?, status = ?, notes = ? WHERE id = ?",
            (borrower_name, borrower_id, quantity, borrow_date, return_date, status, notes, loan_id),
        )
        status_text = "Dipinjam" if new_item_quantity > 0 else "Tersedia"
        self.connection.execute(
            "UPDATE items SET quantity = ?, status = ? WHERE id = ?",
            (new_item_quantity, status_text, loan["item_id"]),
        )
        self.connection.commit()
        return True

    def update_loan_status(self, loan_id, status):
        loan = self.get_loan_by_id(loan_id)
        if loan is None:
            return False

        if status == "Selesai":
            item = self.get_item_by_id(loan["item_id"])
            if item is None:
                return False
            item_quantity = item["quantity"] + loan["quantity"]
            self.connection.execute(
                "UPDATE loans SET status = ? WHERE id = ?",
                (status, loan_id),
            )
            self.connection.execute(
                "UPDATE items SET quantity = ?, status = 'Tersedia' WHERE id = ?",
                (item_quantity, loan["item_id"]),
            )
            self.connection.commit()
            return True

        self.connection.execute("UPDATE loans SET status = ? WHERE id = ?", (status, loan_id))
        self.connection.commit()
        return True

    def get_dashboard_summary(self):
        cursor = self.connection.cursor()
        cursor.execute("SELECT COUNT(*) AS total FROM items")
        total_items = cursor.fetchone()["total"]

        cursor.execute("SELECT COUNT(*) AS available FROM items WHERE status = 'Tersedia'")
        available_items = cursor.fetchone()["available"]

        cursor.execute("SELECT COUNT(*) AS borrowed FROM loans WHERE status = 'Dipinjam'")
        borrowed_items = cursor.fetchone()["borrowed"]

        cursor.execute("SELECT COUNT(*) AS total FROM loans")
        total_loans = cursor.fetchone()["total"]

        cursor.execute("SELECT COUNT(*) AS active FROM loans WHERE status = 'Dipinjam'")
        active_loans = cursor.fetchone()["active"]

        cursor.execute("SELECT COUNT(*) AS completed FROM loans WHERE status = 'Selesai'")
        completed_loans = cursor.fetchone()["completed"]

        return {
            "total_items": total_items,
            "available_items": available_items,
            "borrowed_items": borrowed_items,
            "total_loans": total_loans,
            "active_loans": active_loans,
            "completed_loans": completed_loans,
        }

    def reset_database(self):
        """Clear database tables except user accounts"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            
            for table in tables:
                table_name = table["name"]
                if table_name.lower() not in ['users', 'sqlite_sequence']: 
                    cursor.execute(f"DELETE FROM {table_name}")
                    try:
                        cursor.execute(f"DELETE FROM sqlite_sequence WHERE name='{table_name}'")
                    except:
                        pass
            
            self.connection.commit()
            return True, "Database successfully reset."
        except Exception as e:
            return False, f"Failed to reset database: {e}"
