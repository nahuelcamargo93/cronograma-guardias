import sqlite3
from datetime import date

conn = sqlite3.connect('cronograma_inteligente.db')
c = conn.cursor()

c.execute("SELECT nombre FROM personal WHERE servicio_id = 2 AND COALESCE(activo, 1) = 1")
employees = [r[0] for r in c.fetchall()]

c.execute("SELECT nombre, fecha, turno, horas FROM guardias WHERE cronograma_id = 583")
guardias = c.fetchall()
guardias_by_emp = {}
for name, fecha, turno, horas in guardias:
    guardias_by_emp.setdefault(name, []).append({'fecha': fecha, 'turno': turno, 'horas': horas})

# Transition week days in July: July 27, 28, 29, 30, 31
transition_days = ['2026-07-27', '2026-07-28', '2026-07-29', '2026-07-30', '2026-07-31']
turnos_12h = ['MT', 'TNN']

print("=== ENFERMEROS CON MÁS DE UNA GUARDIA DE 12H EN LA SEMANA DE TRANSICIÓN ===")
found_any = False
for name in employees:
    emp_guards = guardias_by_emp.get(name, [])
    count_12h = 0
    detailed = []
    for g in emp_guards:
        if g['fecha'] in transition_days and g['turno'] in turnos_12h:
            count_12h += 1
            detailed.append(f"{g['fecha']}: {g['turno']}")
            
    if count_12h > 1:
        print(f" - {name}: {count_12h} guardias ({', '.join(detailed)})")
        found_any = True

if not found_any:
    print("Ninguno trabajó más de una guardia de 12h en la semana de transición.")

conn.close()
