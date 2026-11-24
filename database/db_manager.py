from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterable, Optional

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "database" / "expenses.db"
SCHEMA_PATH = PROJECT_ROOT / "database" / "schema.sql"


def get_connection(db_path: Optional[Path | str] = None) -> sqlite3.Connection:
    path = Path(db_path) if db_path else DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def initialize_database(db_path: Optional[Path | str] = None) -> None:
    conn = get_connection(db_path)
    try:
        conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))

        default_categories = [
            ("Lương", "income"), ("Thưởng", "income"), ("Đầu tư", "income"),
            ("Ăn uống", "expense"), ("Di chuyển", "expense"), ("Nhà ở", "expense"),
            ("Mua sắm", "expense"), ("Giải trí", "expense"), ("Sức khỏe", "expense"),
            ("Giáo dục", "expense"), ("Hóa đơn", "expense"), ("Khác", "expense"),
        ]
        conn.executemany(
            "INSERT OR IGNORE INTO categories(name, type) VALUES (?, ?)",
            default_categories,
        )
        conn.commit()
    finally:
        conn.close()


def get_categories(category_type: Optional[str] = None) -> pd.DataFrame:
    conn = get_connection()
    try:
        if category_type:
            return pd.read_sql_query(
                "SELECT * FROM categories WHERE type = ? ORDER BY name",
                conn,
                params=(category_type,),
            )
        return pd.read_sql_query("SELECT * FROM categories ORDER BY type, name", conn)
    finally:
        conn.close()


def add_category(name: str, category_type: str) -> int:
    if category_type not in {"income", "expense"}:
        raise ValueError("Loại danh mục không hợp lệ")
    conn = get_connection()
    try:
        cur = conn.execute(
            "INSERT INTO categories(name, type) VALUES (?, ?)",
            (name.strip(), category_type),
        )
        conn.commit()
        return int(cur.lastrowid)
    finally:
        conn.close()


def delete_category(category_id: int) -> None:
    conn = get_connection()
    try:
        conn.execute("DELETE FROM categories WHERE id = ?", (category_id,))
        conn.commit()
    finally:
        conn.close()


def add_transaction(date: str, description: str, amount: float, tx_type: str,
                    category_id: int, payment_method: str = "Tiền mặt",
                    note: str = "") -> int:
    conn = get_connection()
    try:
        cur = conn.execute(
            """INSERT INTO transactions
               (date, description, amount, type, category_id, payment_method, note)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (date, description.strip(), float(amount), tx_type, int(category_id),
             payment_method, note),
        )
        conn.commit()
        return int(cur.lastrowid)
    finally:
        conn.close()


def update_transaction(transaction_id: int, date: str, description: str, amount: float,
                       tx_type: str, category_id: int, payment_method: str,
                       note: str) -> None:
    conn = get_connection()
    try:
        conn.execute(
            """UPDATE transactions
               SET date=?, description=?, amount=?, type=?, category_id=?,
                   payment_method=?, note=?
               WHERE id=?""",
            (date, description.strip(), float(amount), tx_type, int(category_id),
             payment_method, note, int(transaction_id)),
        )
        conn.commit()
    finally:
        conn.close()


def delete_transaction(transaction_id: int) -> None:
    conn = get_connection()
    try:
        conn.execute("DELETE FROM transactions WHERE id=?", (int(transaction_id),))
        conn.commit()
    finally:
        conn.close()


def get_transactions(start_date: Optional[str] = None,
                     end_date: Optional[str] = None,
                     category_ids: Optional[Iterable[int]] = None,
                     tx_type: Optional[str] = None,
                     search_text: Optional[str] = None) -> pd.DataFrame:
    conn = get_connection()
    try:
        query = """
            SELECT t.id, t.date, t.description, t.amount, t.type,
                   c.name AS category, c.id AS category_id,
                   t.payment_method, t.note
            FROM transactions t
            JOIN categories c ON c.id = t.category_id
            WHERE 1=1
        """
        params: list = []
        if start_date:
            query += " AND t.date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND t.date <= ?"
            params.append(end_date)
        if tx_type:
            query += " AND t.type = ?"
            params.append(tx_type)
        if category_ids:
            placeholders = ",".join("?" for _ in category_ids)
            query += f" AND c.id IN ({placeholders})"
            params.extend(category_ids)
        if search_text:
            query += " AND (t.description LIKE ? OR t.note LIKE ?)"
            needle = f"%{search_text.strip()}%"
            params.extend([needle, needle])
        query += " ORDER BY t.date DESC, t.id DESC"
        return pd.read_sql_query(query, conn, params=params)
    finally:
        conn.close()


def replace_transactions(df: pd.DataFrame) -> int:
    if df.empty:
        return 0
    conn = get_connection()
    inserted = 0
    try:
        conn.execute("DELETE FROM transactions")
        for row in df.itertuples(index=False):
            cur = conn.execute(
                """INSERT INTO transactions
                   (date, description, amount, type, category_id, payment_method, note)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (str(row.date), str(row.description), float(row.amount),
                 str(row.type), int(row.category_id),
                 str(row.payment_method), str(row.note)),
            )
            inserted += cur.rowcount
        conn.commit()
        return inserted
    finally:
        conn.close()


def set_budget(category_id: int, month: str, amount: float) -> None:
    conn = get_connection()
    try:
        conn.execute(
            """INSERT INTO budgets(category_id, month, amount)
               VALUES (?, ?, ?)
               ON CONFLICT(category_id, month) DO UPDATE SET amount=excluded.amount""",
            (int(category_id), month, float(amount)),
        )
        conn.commit()
    finally:
        conn.close()


def get_budgets(month: Optional[str] = None) -> pd.DataFrame:
    conn = get_connection()
    try:
        query = """
            SELECT b.id, b.category_id, c.name AS category, b.month, b.amount
            FROM budgets b JOIN categories c ON c.id=b.category_id
        """
        params = []
        if month:
            query += " WHERE b.month=?"
            params.append(month)
        query += " ORDER BY b.month DESC, c.name"
        return pd.read_sql_query(query, conn, params=params)
    finally:
        conn.close()
