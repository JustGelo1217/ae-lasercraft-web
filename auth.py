from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from database import connect

class User(UserMixin):
    def __init__(self, id, username, role):
        self.id = id
        self.username = username
        self.role = role

def create_user(username, password, role):
    conn = connect()
    c = conn.cursor()
    c.execute(
        "INSERT INTO users VALUES (NULL, ?, ?, ?)",
        (username, generate_password_hash(password), role)
    )
    conn.commit()
    conn.close()

def authenticate(username, password):
    conn = connect()
    c = conn.cursor()
    c.execute("SELECT id, password, role FROM users WHERE username=?", (username,))
    row = c.fetchone()
    conn.close()

    if row and check_password_hash(row[1], password):
        return User(row[0], username, row[2])
    return None
