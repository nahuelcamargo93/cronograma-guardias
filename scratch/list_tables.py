import sqlite3
conn = sqlite3.connect('database/cronograma.db')
cur = conn.cursor()

# List all tables
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cur.fetchall()
print("TABLES:", tables)

conn.close()
