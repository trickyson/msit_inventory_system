# security.py
import bcrypt
from db import get_connection

def hash_password(plain_password: str) -> str:
    """Generate a bcrypt hash (saved as string in DB)."""
    hashed = bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")

def verify_password(plain_password: str, stored_hash: str) -> bool:
    """Verify a plain text password against stored hash string."""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        stored_hash.encode("utf-8")
    )

def is_strong_password(password: str) -> bool:
    """Simple strong password rule."""
    if len(password) < 8:
        return False
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(not c.isalnum() for c in password)
    return has_upper and has_lower and has_digit and has_special

def log_action(user_id, action_type, table_name, record_id, description, ip_address="127.0.0.1"):
    """Insert an entry into the audit_logs table."""
    conn = get_connection()
    cursor = conn.cursor()
    sql = """
        INSERT INTO audit_logs (user_id, action_type, table_name, record_id, description, ip_address)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    cursor.execute(sql, (user_id, action_type, table_name, record_id, description, ip_address))
    conn.commit()
    cursor.close()
    conn.close()
