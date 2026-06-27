from dao.db import get_db_connection
from models import User
from sqlite3 import IntegrityError
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
    except IntegrityError:
        # Email collision handling trap
        return False
    finally:
        conn.close()

def update_user_profile(user_id, first_name, last_name, new_password=None,languages_list=None,role=None):
    """
    Unified function to update any user profile (Guide or Participant).
    """
    conn = get_db_connection()
    try:
        if new_password and languages_list:
            langs_str = ",".join(languages_list) if languages_list else None
            hashed_pw = generate_password_hash(new_password,method='pbkdf2')
            print(f"Updating user_id={user_id} with first_name={first_name}, last_name={last_name}, new_password={'[REDACTED]'}")
            conn.execute(
                "UPDATE users SET first_name = ?, last_name = ?, password_hash = ?, languages = ? WHERE id = ?",
                (first_name, last_name, hashed_pw, langs_str, user_id)
            )
        elif languages_list:
            langs_str = ",".join(languages_list) if languages_list else None
            conn.execute(
                "UPDATE users SET first_name = ?, last_name = ?, languages = ? WHERE id = ?",
                (first_name, last_name, langs_str, user_id)
            )
        else:
            conn.execute(
                "UPDATE users SET first_name = ?, last_name = ? WHERE id = ?",
                (first_name, last_name, user_id)
            )

        if role:
            conn.execute(
                "UPDATE users SET role = ? WHERE id = ?",
                (role, user_id)
            )
        conn.commit()
        return True
    except Exception as e:
        print(f"Database error: {e}")
        return False
    finally:
        conn.close()
