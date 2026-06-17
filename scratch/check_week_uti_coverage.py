import sqlite3
import datetime

conn = sqlite3.connect("cronograma_inteligente.db")
crono_id = 438

# Check all UTI morning assignments for Week 3 (July 13 to 17, 2026)
days = ["2026-07-13", "2026-07-14", "2026-07-15", "2026-07-16", "2026-07-17"]

print("=== COBERTURA MAÑANA_UTI EN SEMANA 3 ===")
for d in days:
    print(f"\nFecha: {d}")
    guards = conn.execute("SELECT nombre, turno FROM guardias WHERE cronograma_id = ? AND fecha = ? AND (turno = 'Mañana_UTI' OR turno = 'Dia_UTI')", (crono_id, d)).fetchall()
    for g in guards:
        print(f"  - {g[0]} ({g[1]})")

# Check all UTI-habilitated personal and their total hours/assignments in that week
print("\n=== PERSONAL HABILITADO UTI Y SUS ASIGNACIONES EN SEMANA 3 ===")
personal = conn.execute("""
    SELECT DISTINCT p.nombre, p.rol 
    FROM personal p
    JOIN personal_puestos pp ON p.nombre = pp.personal_nombre
    JOIN puestos pst ON pp.puesto_id = pst.id
    WHERE pst.nombre = 'UTI' AND p.servicio_id = 1 AND p.activo = 1
""").fetchall()

for p_nom, p_rol in sorted(personal):
    w_guards = conn.execute("SELECT fecha, turno FROM guardias WHERE cronograma_id = ? AND nombre = ? AND fecha BETWEEN '2026-07-13' AND '2026-07-19' ORDER BY fecha", (crono_id, p_nom)).fetchall()
    print(f"{p_nom} ({p_rol}): {len(w_guards)} guardias")
    for g in w_guards:
        print(f"  - {g[0]}: {g[1]}")

conn.close()
