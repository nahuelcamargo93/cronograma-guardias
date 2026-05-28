import sqlite3
import json

conn = sqlite3.connect("cronograma_inteligente.db")
cursor = conn.cursor()

# Query employees and their puestos
cursor.execute("""
    SELECT p.nombre, p.rol, p.puestos_habilitados_json, p.puestos_primarios_json
    FROM personal p
    WHERE p.servicio_id = 3 AND p.activo = 1
""")
rows = cursor.fetchall()
print(f"{'Name':35} | {'Rol':15} | {'Habilitados':30} | {'Primarios':30}")
print("-" * 120)
for r in rows:
    print(f"{r[0]:35} | {r[1]:15s} | {str(r[2]):30s} | {str(r[3]):30s}")
conn.close()
