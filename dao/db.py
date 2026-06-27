import sqlite3

def get_db_connection():
    """
    Establishes an active database session context using the absolute path.
    """
    # Absolute path to your database on PythonAnywhere
    db_path = 'database.db'
    
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    return conn