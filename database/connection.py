import sqlite3
import os

DB_NAME = os.getenv("USE_TEMP_DB", "cronograma_inteligente.db")
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), DB_NAME)

def get_connection():
    conn = sqlite3.connect(DB_PATH, timeout=60.0)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn
