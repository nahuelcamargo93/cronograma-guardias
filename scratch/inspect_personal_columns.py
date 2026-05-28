import sqlite3

conn = sqlite3.connect("cronograma_inteligente.db")
cursor = conn.cursor()
cursor.execute("SELECT * FROM personal LIMIT 1")
col_names = [description[0] for description in cursor.description]
print("Columns in personal:", col_names)
conn.close()
