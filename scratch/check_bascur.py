import sys
sys.path.insert(0, '.')
import sqlite3
from database.data_loader import obtener_empleados
import database.queries as db_queries

conn = sqlite3.connect('cronograma_inteligente.db')

try:
    servicio_id = 2
    fecha_inicio = "2026-08-01"
    dias_del_bloque = 31

    empleados = obtener_empleados(servicio_id, fecha_inicio, dias_del_bloque)
    bascur = next(e for e in empleados if 'BASCUR' in e.nombre)
    print("=== Bascur Alejandra ===")
    print("Nombre:", bascur.nombre)
    print("Rol:", bascur.rol)
    print("Licencias:", bascur.dias_licencia)
    print("Puestos habilitados:", bascur.puestos_habilitados)
    print("Reglas:")
    for k, v in bascur.reglas.items():
        print(f"  {k}: {v}")

    # Consultar personal_reglas de la DB
    print("\n=== personal_reglas in DB ===")
    rows = conn.execute("SELECT * FROM personal_reglas WHERE personal_nombre = ?", (bascur.nombre,)).fetchall()
    for r in rows:
        print(r)

    # Consultar personal_reglas_ajustes de la DB
    print("\n=== personal_reglas_ajustes in DB ===")
    rows2 = conn.execute("SELECT * FROM personal_reglas_ajustes WHERE personal_nombre = ?", (bascur.nombre,)).fetchall()
    for r in rows2:
        print(r)

finally:
    conn.close()
