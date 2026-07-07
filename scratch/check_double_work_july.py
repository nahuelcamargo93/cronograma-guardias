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

print("=== VERIFICANDO COLISIÓN DE TRANSICIÓN EN JULIO ===")
found_any = False
for name in employees:
    emp_guards = guardias_by_emp.get(name, [])
    
    # Week July 20
    cat_july20 = determinar_familia_ganadora(emp_guards, date.fromisoformat('2026-07-20'))
    # Week July 27
    cat_july27 = determinar_familia_ganadora(emp_guards, date.fromisoformat('2026-07-27'))
    
    for fam in ['N', 'TN']:
        if cat_july20 == fam and cat_july27 == fam:
            print(f" - {name} trabajó {fam} en la semana del 20-Jul Y en la semana del 27-Jul (historial fijo de Julio)!")
            found_any = True

if not found_any:
    print("Ningún enfermero tiene asignaciones consecutivas en las semanas del 20-Jul y 27-Jul.")

conn.close()
