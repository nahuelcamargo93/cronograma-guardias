import sqlite3
from datetime import date
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

print("=== CHECKING ALL TRANSITION WINDOW CLASHES IN JULY ===")
clashing_employees = set()

for name in employees:
    emp_guards = guardias_by_emp.get(name, [])
    
    cats = {}
    for w in ['2026-07-06', '2026-07-13', '2026-07-20', '2026-07-27']:
        cats[w] = determinar_familia_ganadora(emp_guards, date.fromisoformat(w))
        
    for fam in ['N', 'TN']:
        if cats['2026-07-27'] == fam:
            # Check window July 20
            if cats['2026-07-20'] == fam:
                print(f" - {name}: Clash {fam} in July 20 & July 27")
                clashing_employees.add((fam, name))
            # Check window July 13
            if cats['2026-07-13'] == fam:
                print(f" - {name}: Clash {fam} in July 13 & July 27")
                clashing_employees.add((fam, name))
            # Check window July 6
            if cats['2026-07-06'] == fam:
                print(f" - {name}: Clash {fam} in July 06 & July 27")
                clashing_employees.add((fam, name))

print("\nUnique clashing (rule, employee) pairs:")
print(list(clashing_employees))

conn.close()
