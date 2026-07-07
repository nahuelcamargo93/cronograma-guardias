import sqlite3
from datetime import date, timedelta
import sys
sys.path.append('.')
from restricciones.hard._utils import determinar_familia_ganadora

conn = sqlite3.connect('cronograma_inteligente.db')
c = conn.cursor()

c.execute("SELECT nombre FROM personal WHERE servicio_id = 2 AND COALESCE(activo, 1) = 1")
employees = [r[0] for r in c.fetchall()]

c.execute("SELECT nombre, fecha, turno, horas FROM guardias WHERE cronograma_id = 583")
guardias = c.fetchall()
guardias_by_emp = {}
for name, fecha, turno, horas in guardias:
    guardias_by_emp.setdefault(name, []).append({'fecha': fecha, 'turno': turno, 'horas': horas})

# Employees who worked TN in July 20 and July 27
worked_july_20_27 = set()
for name in employees:
    emp_guards = guardias_by_emp.get(name, [])
    for w in ['2026-07-20', '2026-07-27']:
        w_dt = date.fromisoformat(w)
        if determinar_familia_ganadora(emp_guards, w_dt) == 'TN':
            worked_july_20_27.add(name)

print(f"Unique employees who worked TN in the weeks of July 20 and July 27: {len(worked_july_20_27)}")

# In the week of Aug 3, we must assign at least 10 employees to TN to cover 49 shifts (since each can work at most 5 shifts).
# These 10 employees must be chosen from the 15 clean employees of Aug 3.
# The 15 clean employees of Aug 3 did NOT work TN in July 13, July 20, or July 27.
# So the 10 assigned on Aug 3 have 0 overlap with July 20 and July 27.
# Therefore, in the week of Aug 10, the total unique employees who worked TN in (July 20, July 27, Aug 3) is:
# len(worked_july_20_27) + 10.
print(f"Total blocked employees for the week of Aug 10: {len(worked_july_20_27)} + 10 = {len(worked_july_20_27) + 10}")
print(f"Clean employees left for the week of Aug 10: 52 - {len(worked_july_20_27) + 10} = {52 - (len(worked_july_20_27) + 10)}")

conn.close()
