import sys; sys.path.append('.')
from database.connection import get_connection

conn = get_connection()

# Check if personal_franco_forzado table exists
tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
print("=== Tables with 'franco' or 'fija' ===")
for t in tables:
    if 'franco' in t.lower() or 'fija' in t.lower() or 'asignacion' in t.lower():
        print(f"  {t}")
        count = conn.execute(f"SELECT COUNT(*) FROM [{t}]").fetchone()[0]
        print(f"    -> {count} rows")

print("\n=== personal_asignaciones_fijas for servicio 1 ===")
try:
    rows = conn.execute("""
        SELECT paf.* FROM personal_asignaciones_fijas paf
        JOIN personal p ON paf.personal_nombre = p.nombre
        WHERE p.servicio_id = 1 AND paf.activo = 1
    """).fetchall()
    for r in rows:
        print(r)
except Exception as e:
    print(f"Error: {e}")

print("\n=== personal_franco_forzado for servicio 1 (if exists) ===")
try:
    rows = conn.execute("""
        SELECT pff.* FROM personal_franco_forzado pff
        JOIN personal p ON pff.personal_nombre = p.nombre
        WHERE p.servicio_id = 1 AND pff.activo = 1
    """).fetchall()
    for r in rows:
        print(r)
except Exception as e:
    print(f"Table doesn't exist or error: {e}")

conn.close()
