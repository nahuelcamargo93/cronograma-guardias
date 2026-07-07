import sys, os
sys.path.append(os.getcwd())
from database.connection import get_connection

conn = get_connection()
cursor = conn.cursor()
cursor.execute("SELECT * FROM personal_reglas_ajustes WHERE fecha_inicio <= '2026-08-31' AND fecha_fin >= '2026-08-01'")
for r in cursor.fetchall():
    print(r)
conn.close()
