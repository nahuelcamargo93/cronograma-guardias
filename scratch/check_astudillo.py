import sqlite3

conn = sqlite3.connect('cronograma_inteligente.db')
c = conn.cursor()

print("=== Asignaciones Fijas Agosto 2026 (Servicio 2) ===")
c.execute("""
    SELECT paf.personal_nombre, paf.fecha, paf.dia_semana, paf.turno
    FROM personal_asignaciones_fijas paf
    JOIN personal p ON paf.personal_nombre = p.nombre
    WHERE p.servicio_id = 2 AND paf.activo = 1
""")
for r in c.fetchall():
    print(r)

print("\n=== Francos Forzados Agosto 2026 (Servicio 2) ===")
c.execute("""
    SELECT pff.personal_nombre, pff.fecha_inicio, pff.fecha_fin
    FROM personal_francos_forzados pff
    JOIN personal p ON pff.personal_nombre = p.nombre
    WHERE p.servicio_id = 2 AND pff.activo = 1 AND pff.fecha_inicio <= '2026-08-31' AND pff.fecha_fin >= '2026-08-01'
""")
for r in c.fetchall():
    print(r)

conn.close()
