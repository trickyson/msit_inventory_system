# security.py
import re
import bcrypt
from werkzeug.security import check_password_hash
from db import get_connection

# ---------- PASSWORD HELPERS ----------

def hash_password(plain_password: str) -> str:
    """
    Hash a password using bcrypt for new accounts.
    """
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(plain_password.encode("utf-8"), salt)
    # store as utf-8 string
    return hashed.decode("utf-8")


def verify_password(plain_password: str, stored_hash: str) -> bool:
    """
    Verify password for BOTH:
      - old PBKDF2 hashes (starting with 'pbkdf2:')
      - new bcrypt hashes
    """
    if not stored_hash:
        return False

    # OLD HASHES: pbkdf2 (from Werkzeug)
    if stored_hash.startswith("pbkdf2:"):
        # stored_hash = pbkdf2:sha256:...
        try:
            return check_password_hash(stored_hash, plain_password)
        except Exception:
            return False

    # NEW HASHES: bcrypt
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            stored_hash.encode("utf-8"),
        )
    except Exception:
        # includes ValueError: Invalid salt, etc.
        return False


def is_strong_password(password: str) -> bool:
    """
    Check if password is at least 8 chars,
    with upper, lower, digit, and special char.
    """
    if len(password) < 8:
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"[a-z]", password):
        return False
    if not re.search(r"\d", password):
        return False
    if not re.search(r"[^A-Za-z0-9]", password):
        return False
    return True

# ---------- AUDIT LOGGING ----------

def log_action(user_id, action, table_name, record_id, details):
    """
    Insert a row into inventory_logs for audit trail.
    """
    conn = get_connection()
    cursor = conn.cursor()

    sql = """
        INSERT INTO inventory_logs (user_id, action, table_name, record_id, details)
        VALUES (%s, %s, %s, %s, %s)
    """

    try:
        cursor.execute(sql, (user_id, action, table_name, record_id, details))
        conn.commit()
    except Exception:
        conn.rollback()
    finally:
        cursor.close()
        conn.close()
