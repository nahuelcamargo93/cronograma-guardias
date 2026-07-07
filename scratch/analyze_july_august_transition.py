import sqlite3
from datetime import date, timedelta
import sys
sys.path.append('.')
from restricciones.hard._utils import determinar_familia_ganadora

conn = sqlite3.connect('cronograma_inteligente.db')
c = conn.cursor()

c.execute("SELECT nombre FROM personal WHERE servicio_id = 2 AND COALESCE(activo, 1) = 1")
employees = [r[0] for r in c.fetchall()]

# Guardias of July 583 and August 610
c.execute("SELECT nombre, fecha, turno, horas FROM guardias WHERE cronograma_id IN (583, 610)")
guardias = c.fetchall()

guardias_by_emp = {}
for name, fecha, turno, horas in guardias:
    guardias_by_emp.setdefault(name, []).append({'fecha': fecha, 'turno': turno, 'horas': horas})

# Let's check for Turno Noche (N)
print("=== ANÁLISIS DE DISPONIBILIDAD PARA EL TURNO NOCHE (N) ===")

# For the week of Aug 3, an employee is "clean" if they did not work N in the weeks of:
# July 13, July 20, July 27
weeks_to_check = ['2026-07-13', '2026-07-20', '2026-07-27']

worked_n_in_prev = set()
for name in employees:
    emp_guards = guardias_by_emp.get(name, [])
    worked_recently = False
    for w in weeks_to_check:
        w_dt = date.fromisoformat(w)
        cat = determinar_familia_ganadora(emp_guards, w_dt)
        if cat == 'N':
            worked_recently = True
            break
    if worked_recently:
        worked_n_in_prev.add(name)

clean_for_aug3 = [name for name in employees if name not in worked_n_in_prev]

print(f"Total empleados: {len(employees)}")
print(f"Empleados que trabajaron N en las últimas 3 semanas de Julio: {len(worked_n_in_prev)}")
print(f"Empleados libres de N para la semana de Aug 3: {len(clean_for_aug3)}")
print(f"Capacidad máxima de guardias N que pueden cubrir los libres (a 5 turnos/semana c/u): {len(clean_for_aug3) * 5}")
print(f"Demanda semanal mínima de turnos N: 49")

if len(clean_for_aug3) * 5 < 49:
    print(f"\n=> ¡MATEMÁTICAMENTE IMPOSIBLE sin violaciones! Falta capacidad para cubrir {49 - len(clean_for_aug3) * 5} turnos N.")
else:
    print("\n=> Hay capacidad suficiente teórica, pero otros factores (licencias, descansos, etc.) podrían influir.")


# Let's do the same for Tarde Noche (TN)
print("\n=== ANÁLISIS DE DISPONIBILIDAD PARA TARDE NOCHE (TN) ===")
worked_tn_in_prev = set()
for name in employees:
    emp_guards = guardias_by_emp.get(name, [])
    worked_recently = False
    for w in weeks_to_check:
        w_dt = date.fromisoformat(w)
        cat = determinar_familia_ganadora(emp_guards, w_dt)
        if cat == 'TN':
            worked_recently = True
            break
    if worked_recently:
        worked_tn_in_prev.add(name)

clean_for_aug3_tn = [name for name in employees if name not in worked_tn_in_prev]

print(f"Empleados que trabajaron TN en las últimas 3 semanas de Julio: {len(worked_tn_in_prev)}")
print(f"Empleados libres de TN para la semana de Aug 3: {len(clean_for_aug3_tn)}")
print(f"Capacidad máxima de guardias TN que pueden cubrir los libres (a 5 turnos/semana c/u): {len(clean_for_aug3_tn) * 5}")
print(f"Demanda semanal mínima de turnos TN: 49")

if len(clean_for_aug3_tn) * 5 < 49:
    print(f"\n=> ¡MATEMÁTICAMENTE IMPOSIBLE sin violaciones! Falta capacidad para cubrir {49 - len(clean_for_aug3_tn) * 5} turnos TN.")
else:
    print("\n=> Hay capacidad suficiente teórica.")

conn.close()
