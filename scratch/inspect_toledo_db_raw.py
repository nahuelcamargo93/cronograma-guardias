import sys, os
sys.path.append(os.getcwd())
from database.connection import get_connection

conn = get_connection()
cursor = conn.cursor()
cursor.execute("SELECT * FROM personal_reglas_ajustes WHERE personal_nombre LIKE '%Toledo%'")
for r in cursor.fetchall():
    print(r)
conn.close()
