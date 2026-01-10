from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from database import connect

class User(UserMixin):
    def __init__(self, id, username, role, is_active=1):
        self.id = id
        self.username = username
        self.role = role
        self._is_active = bool(is_active)

    @property
    def is_active(self):
        return self._is_active


def create_user(username, password, role):
    conn = connect()
    c = conn.cursor()
    c.execute(
        "INSERT INTO users VALUES (NULL, %s, %s, %s)",
        (username, generate_password_hash(password), role)
    )
    conn.commit()
    conn.close()

def authenticate(username, password):
    conn = connect()
    c = conn.cursor()

    c.execute("""
        SELECT id, username, password, role, is_active
        FROM users
        WHERE LOWER(username) = LOWER(%s)
        LIMIT 1
    """, (username,))

    row = c.fetchone()
    conn.close()

    if not row:
        return None

    user_id, db_username, password_hash, role, is_active = row

    if not check_password_hash(password_hash, password):
        return None

    return User(user_id, db_username, role, is_active)

