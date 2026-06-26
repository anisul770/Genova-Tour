import os
import sqlite3

def get_db_connection():
    """
    Establishes an active database session context.
    Enforces foreign keys explicitly and provisions dictionaries for row mappings.
    """
    db_path = os.getenv("DATABASE_PATH")
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    return conn