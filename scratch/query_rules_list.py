import sqlite3
import json
import os

db_path = 'cronograma_inteligente.db'
print(f"Connecting to database at {db_path}...")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("\n--- REGLAS EN EL CATÁLOGO ---")
rules_catalogo = cursor.execute("SELECT codigo_regla, tipo, descripcion FROM reglas_catalogo").fetchall()
for rc in rules_catalogo:
    print(f"Code: {rc[0]} | Type: {rc[1]} | Desc: {rc[2]}")

print("\n--- REGLAS DEL SERVICIO 1 ---")
rules_serv = cursor.execute("SELECT codigo_regla, activo, parametros_json FROM servicios_reglas WHERE servicio_id = 1").fetchall()
for rs in rules_serv:
    print(f"Code: {rs[0]} | Activo: {rs[1]} | Params: {rs[2]}")

print("\n--- REGLAS INDIVIDUALES DEL PERSONAL (SERVICIO 1) ---")
rules_pers = cursor.execute("""
    SELECT pr.personal_nombre, pr.codigo_regla, pr.activo, pr.parametros_json
    FROM personal_reglas pr
    JOIN personal p ON pr.personal_nombre = p.nombre
    WHERE p.servicio_id = 1
""").fetchall()
for rp in rules_pers:
    print(f"Emp: {rp[0]} | Code: {rp[1]} | Activo: {rp[2]} | Params: {rp[3]}")

conn.close()
