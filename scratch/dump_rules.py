import sqlite3
import json

conn = sqlite3.connect("cronograma_inteligente.db")
cursor = conn.cursor()

print("--- REGLAS DE PERSONAL ---")
rows = cursor.execute("SELECT personal_nombre, regla_id, parametros_json FROM personal_reglas").fetchall()
for r in rows:
    # Get regla name
    regla_name = cursor.execute("SELECT codigo_regla FROM reglas_catalogo WHERE id = ?", (r[1],)).fetchone()[0]
    print(f"Empleado: {r[0]} | Regla: {regla_name} | Params: {r[2]}")

print("\n--- REGLAS DE SERVICIO (ID 2) ---")
rows_serv = cursor.execute("SELECT rc.codigo_regla, sr.parametros_json FROM servicio_reglas sr JOIN reglas_catalogo rc ON sr.regla_id = rc.id WHERE sr.servicio_id = 2").fetchall()
for r in rows_serv:
    print(f"Regla: {r[0]} | Params: {r[1]}")

conn.close()
