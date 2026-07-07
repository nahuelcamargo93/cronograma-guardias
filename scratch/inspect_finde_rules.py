import sys; sys.path.append('.')
from database.connection import get_connection

conn = get_connection()
print("=== servicios_reglas FINDE* servicio 1 ===")
for r in conn.execute("SELECT codigo_regla, parametros_json FROM servicios_reglas WHERE servicio_id=1 AND activo=1 AND codigo_regla LIKE '%FINDE%'").fetchall():
    print(r[0], "->", r[1][:200] if r[1] else None)

print("\n=== organizaciones_reglas FINDE* ===")
for r in conn.execute("SELECT codigo_regla, parametros_json FROM organizaciones_reglas WHERE activo=1 AND codigo_regla LIKE '%FINDE%'").fetchall():
    print(r[0], "->", r[1][:200] if r[1] else None)

print("\n=== servicios_reglas MANEJO_FINDES servicio 1 ===")
for r in conn.execute("SELECT codigo_regla, parametros_json FROM servicios_reglas WHERE servicio_id=1 AND activo=1 AND codigo_regla LIKE '%MANEJO%'").fetchall():
    print(r[0], "->", r[1][:300] if r[1] else None)

print("\n=== organizaciones_reglas MANEJO_FINDES ===")
for r in conn.execute("SELECT codigo_regla, parametros_json FROM organizaciones_reglas WHERE activo=1 AND codigo_regla LIKE '%MANEJO%'").fetchall():
    print(r[0], "->", r[1][:300] if r[1] else None)

conn.close()
