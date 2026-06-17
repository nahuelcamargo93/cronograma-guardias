import sqlite3
from database.connection import get_connection

with get_connection() as conn:
    rows = conn.execute("SELECT id, personal_nombre, codigo_regla, parametros_json, activo FROM personal_reglas WHERE personal_nombre LIKE '%Giaccoppo%'").fetchall()
    for r in rows:
        print(f"ID: {r[0]}, Nombre: {r[1]}, Regla: {r[2]}, Params: {r[3]}, Activo: {r[4]}")
