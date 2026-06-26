from dao.db import get_db_connection
from models import User
from werkzeug.security import generate_password_hash, check_password_hash

def get_user_by_id(user_id):
    conn = get_db_connection()
    row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    if not row:
        return None
    langs = row['languages'].split(',') if row['languages'] else []
    return User(row['id'], row['email'], row['first_name'], row['last_name'], row['role'], langs)

def get_user_by_email(email):
    conn = get_db_connection()
    row = conn.execute("SELECT * FROM users WHERE email = ?", (email.strip().lower(),)).fetchone()
    conn.close()
    if not row:
        return None
    langs = row['languages'].split(',') if row['languages'] else []
    return User(row['id'], row['email'], row['first_name'], row['last_name'], row['role'], langs)

def verify_user_credentials(email, password):
    conn = get_db_connection()
    row = conn.execute("SELECT * FROM users WHERE email = ?", (email.strip().lower(),)).fetchone()
    conn.close()
    if row and check_password_hash(row['password_hash'], password):
        langs = row['languages'].split(',') if row['languages'] else []
        return User(row['id'], row['email'], row['first_name'], row['last_name'], row['role'], langs)
    return None

def register_new_user(email, password, first_name, last_name, role, languages_list=None):
    conn = get_db_connection()
    pwd_hash = generate_password_hash(password, method='pbkdf2')
    langs_str = ",".join(languages_list) if languages_list else None
    
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (email, password_hash, first_name, last_name, role, languages) VALUES (?, ?, ?, ?, ?, ?)",
            (email.strip().lower(), pwd_hash, first_name.strip(), last_name.strip(), role, langs_str)
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        # Email collision handling trap
        return False
    finally:
        conn.close()