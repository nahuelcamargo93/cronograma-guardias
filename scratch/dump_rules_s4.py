import sqlite3
import json
import sys
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from database.connection import get_connection

with get_connection() as conn:
    print("--- Reglas en servicios_reglas para servicio_id = 4 ---")
    rows = conn.execute("SELECT codigo_regla, parametros_json, activo FROM servicios_reglas WHERE servicio_id = 4").fetchall()
    for row in rows:
        print(f"Regla: {row[0]}, Parámetros: {row[1]}, Activo: {row[2]}")

    print("\n--- Reglas en reglas_catalogo ---")
    rows2 = conn.execute("SELECT codigo_regla, tipo, descripcion FROM reglas_catalogo WHERE codigo_regla LIKE '%EQUIDAD%'").fetchall()
    for row in rows2:
        print(f"Regla: {row[0]}, Tipo: {row[1]}, Desc: {row[2]}")
