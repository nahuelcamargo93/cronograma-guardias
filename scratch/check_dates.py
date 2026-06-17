import sqlite3

conn = sqlite3.connect("cronograma_inteligente.db")
cursor = conn.cursor()

print("--- Services ---")
cursor.execute("SELECT id, nombre FROM servicios")
for row in cursor.fetchall():
    print(row)

print("\n--- Date formats of FRANCO_FORZADO ---")
cursor.execute("SELECT DISTINCT fecha_inicio, fecha_fin FROM personal_reglas_ajustes WHERE codigo_regla = 'FRANCO_FORZADO' LIMIT 15")
for row in cursor.fetchall():
    print(row)

conn.close()
