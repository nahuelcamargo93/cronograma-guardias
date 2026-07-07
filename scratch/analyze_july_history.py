import sqlite3
from datetime import date, timedelta
import sys
sys.path.append('.')
from restricciones.hard._utils import determinar_familia_ganadora

conn = sqlite3.connect('cronograma_inteligente.db')
c = conn.cursor()

c.execute("SELECT nombre FROM personal WHERE servicio_id = 2 AND COALESCE(activo, 1) = 1")
employees = [r[0] for r in c.fetchall()]

c.execute("SELECT nombre, fecha, turno FROM guardias WHERE cronograma_id = 583")
guardias = c.fetchall()

guardias_by_emp = {}
for name, fecha, turno in guardias:
    guardias_by_emp.setdefault(name, []).append({'fecha': fecha, 'turno': turno})

july_weeks = ['2026-07-06', '2026-07-13', '2026-07-20', '2026-07-27']

print("=== DISTRIBUCIÓN DE CATEGORÍAS EN JULIO (CRONOGRAMA 583) ===")
counts = {w: {'M': 0, 'T': 0, 'TN': 0, 'N': 0, None: 0} for w in july_weeks}

for name in sorted(employees):
    emp_guards = guardias_by_emp.get(name, [])
    for w in july_weeks:
        w_dt = date.fromisoformat(w)
        # For 2026-07-27 we only look at July 27-31
        cat = determinar_familia_ganadora(emp_guards, w_dt)
        counts[w][cat] = counts[w].get(cat, 0) + 1

for w in july_weeks:
    print(f"Semana {w}:")
    for cat, cnt in counts[w].items():
        print(f"  {cat or 'Ninguno'}: {cnt}")
    print()

conn.close()
