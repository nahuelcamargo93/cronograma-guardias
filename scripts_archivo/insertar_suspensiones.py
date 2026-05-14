import sys
sys.path.insert(0, '.')
import db

# Crear la tabla si no existe
db.inicializar_db()

conn = db.get_connection()

# Suspender ASIGNACION_FIJA para Coniglio, Giaccoppo y Camargo
# en las semanas criticas 1 y 2 (01/06 - 14/06)
# Para la semana 3 (15/06), Coniglio ya esta de LPP, pero Giaccoppo y Camargo siguen activos
suspensiones = [
    ('Lic. Coniglio',    'ASIGNACION_FIJA', '2026-06-01', '2026-06-14', 'SUSPENDER'),
    ('Lic. Giaccoppo',   'ASIGNACION_FIJA', '2026-06-01', '2026-06-21', 'SUSPENDER'),
    ('Lic. Camargo N.',  'ASIGNACION_FIJA', '2026-06-01', '2026-06-21', 'SUSPENDER'),
]

# Limpiar suspensiones previas
conn.execute("DELETE FROM personal_reglas_ajustes WHERE codigo_regla = 'ASIGNACION_FIJA'")

for nombre, codigo, fi, ff, accion in suspensiones:
    conn.execute("""
        INSERT INTO personal_reglas_ajustes (personal_nombre, codigo_regla, fecha_inicio, fecha_fin, accion)
        VALUES (?, ?, ?, ?, ?)
    """, (nombre, codigo, fi, ff, accion))

conn.commit()

print("Suspensiones aplicadas:")
rows = conn.execute("SELECT personal_nombre, codigo_regla, fecha_inicio, fecha_fin, accion FROM personal_reglas_ajustes").fetchall()
for r in rows:
    print(f"  {r[0]:<20} | {r[1]:<18} | {r[2]} -> {r[3]} | {r[4]}")
conn.close()
