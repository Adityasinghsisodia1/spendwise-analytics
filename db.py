"""SQLite repository for expenses — the only module that knows about sqlite3.

Callers (app.py, export.py) work with dicts/DataFrames and never build SQL
themselves, so the storage engine could be swapped later without touching
the UI or export logic.
"""

import sqlite3
from datetime import date
from pathlib import Path

DB_PATH = Path(__file__).parent / "expenses.db"

CATEGORIES = [
    "Food",
    "Transport",
    "Utilities",
    "Rent",
    "Entertainment",
    "Health",
    "Shopping",
    "Other",
]


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                expense_date TEXT NOT NULL,
                category TEXT NOT NULL,
                description TEXT,
                amount REAL NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        # Speeds up the monthly/category aggregations below once the table
        # grows past a trivial number of rows.
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_expenses_date ON expenses(expense_date)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_expenses_category ON expenses(category)"
        )


def add_expense(expense_date: date, category: str, description: str, amount: float) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO expenses (expense_date, category, description, amount)
            VALUES (?, ?, ?, ?)
            """,
            (expense_date.isoformat(), category, description, amount),
        )


def delete_expense(expense_id: int) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))


def list_expenses(month: str | None = None, category: str | None = None) -> list[sqlite3.Row]:
    """List expenses, optionally filtered by month ('YYYY-MM') and/or category."""
    query = "SELECT * FROM expenses WHERE 1=1"
    params: list[str] = []

    if month:
        query += " AND expense_date LIKE ?"
        params.append(f"{month}%")
    if category:
        query += " AND category = ?"
        params.append(category)

    query += " ORDER BY expense_date DESC, id DESC"

    with get_connection() as conn:
        return conn.execute(query, params).fetchall()


def get_available_months() -> list[str]:
    """Distinct 'YYYY-MM' months that have at least one expense, most recent first."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT DISTINCT substr(expense_date, 1, 7) AS month FROM expenses "
            "ORDER BY month DESC"
        ).fetchall()
    return [row["month"] for row in rows]


def get_category_totals(month: str | None = None) -> list[sqlite3.Row]:
    """Total spent per category, aggregated in SQL (not looped in Python)."""
    query = "SELECT category, SUM(amount) AS total FROM expenses WHERE 1=1"
    params: list[str] = []

    if month:
        query += " AND expense_date LIKE ?"
        params.append(f"{month}%")

    query += " GROUP BY category ORDER BY total DESC"

    with get_connection() as conn:
        return conn.execute(query, params).fetchall()


def get_monthly_totals() -> list[sqlite3.Row]:
    """Total spent per month across all history, for the trend chart."""
    with get_connection() as conn:
        return conn.execute(
            """
            SELECT substr(expense_date, 1, 7) AS month, SUM(amount) AS total
            FROM expenses
            GROUP BY month
            ORDER BY month ASC
            """
        ).fetchall()
