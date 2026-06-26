import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

DATABASE_URL = os.getenv("DATABASE_URL")


def get_conn():
    return psycopg2.connect(DATABASE_URL)


def init_db():
    """Create all tables if they don't exist."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            # Financials categories
            cur.execute("""
                CREATE TABLE IF NOT EXISTS fin_categories (
                    id         TEXT PRIMARY KEY,
                    name       TEXT NOT NULL,
                    color      TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)

            # Financials entries
            cur.execute("""
                CREATE TABLE IF NOT EXISTS fin_entries (
                    id          TEXT PRIMARY KEY,
                    category_id TEXT NOT NULL,
                    amount      NUMERIC(10,2) NOT NULL,
                    month       TEXT NOT NULL,
                    note        TEXT DEFAULT '',
                    created_at  TIMESTAMP DEFAULT NOW()
                )
            """)

            # Key-value store for benchmarks and other settings
            cur.execute("""
                CREATE TABLE IF NOT EXISTS kv_store (
                    key        TEXT PRIMARY KEY,
                    value      TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT NOW()
                )
            """)

            conn.commit()

    # Seed default categories if empty
    seed_default_categories()
    print("Database initialized ✅")


def seed_default_categories():
    """Insert default categories if none exist."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM fin_categories")
            count = cur.fetchone()[0]
            if count == 0:
                defaults = [
                    ("cat_1", "Editor Salary", "#3b82f6"),
                    ("cat_2", "Riverside",     "#f97316"),
                    ("cat_3", "CapCut",        "#a78bfa"),
                    ("cat_4", "Canva",         "#22c55e"),
                ]
                for cat in defaults:
                    cur.execute(
                        "INSERT INTO fin_categories (id, name, color) VALUES (%s, %s, %s)",
                        cat
                    )
                conn.commit()


# ── Categories ────────────────────────────────────────────────────────────────

def get_categories():
    with get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM fin_categories ORDER BY created_at")
            return [dict(r) for r in cur.fetchall()]


def add_category(cat_id, name, color):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO fin_categories (id, name, color) VALUES (%s, %s, %s)",
                (cat_id, name, color)
            )
            conn.commit()


def update_category(cat_id, name, color):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE fin_categories SET name=%s, color=%s WHERE id=%s",
                (name, color, cat_id)
            )
            conn.commit()


def delete_category(cat_id):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM fin_entries    WHERE category_id=%s", (cat_id,))
            cur.execute("DELETE FROM fin_categories WHERE id=%s",          (cat_id,))
            conn.commit()


# ── Entries ───────────────────────────────────────────────────────────────────

def get_entries():
    with get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM fin_entries ORDER BY month DESC, created_at DESC")
            rows = cur.fetchall()
            result = []
            for r in rows:
                d = dict(r)
                d["amount"]     = float(d["amount"])
                d["created_at"] = str(d["created_at"])[:19]
                result.append(d)
            return result


def add_entry(entry_id, category_id, amount, month, note):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO fin_entries (id, category_id, amount, month, note)
                   VALUES (%s, %s, %s, %s, %s)""",
                (entry_id, category_id, float(amount), month, note)
            )
            conn.commit()


def delete_entry(entry_id):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM fin_entries WHERE id=%s", (entry_id,))
            conn.commit()


# ── KV Store (benchmarks etc) ─────────────────────────────────────────────────

def kv_get(key):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT value FROM kv_store WHERE key=%s", (key,))
            row = cur.fetchone()
            return json.loads(row[0]) if row else None


def kv_set(key, value):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO kv_store (key, value, updated_at)
                VALUES (%s, %s, NOW())
                ON CONFLICT (key) DO UPDATE
                SET value = EXCLUDED.value, updated_at = NOW()
            """, (key, json.dumps(value)))
            conn.commit()