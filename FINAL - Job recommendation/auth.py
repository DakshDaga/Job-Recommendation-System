# auth.py
import streamlit as st
import sqlite3
import hashlib
import os
from dotenv import load_dotenv

load_dotenv()


def init_db():
    conn = sqlite3.connect('career_app.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE,
                  email TEXT UNIQUE,
                  password_hash TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()


def hash_password(password):
    salt = os.getenv("PASSWORD_SALT", "default_salt")
    return hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000).hex()

# User registration
def register_user(username, email, password):
    conn = sqlite3.connect('career_app.db')
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
                 (username, email, hash_password(password)))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

# User login
def verify_user(username, password):
    conn = sqlite3.connect('career_app.db')
    c = conn.cursor()
    c.execute("SELECT password_hash FROM users WHERE username = ?", (username,))
    result = c.fetchone()
    conn.close()
    if result:
        return result[0] == hash_password(password)
    return False

def delete_user_data(user_id):
    """Permanently delete user's response data"""
    conn = sqlite3.connect('career_app.db')
    c = conn.cursor()
    try:
        c.execute("DELETE FROM user_responses WHERE user_id = ?", (user_id,))
        conn.commit()
    finally:
        conn.close()