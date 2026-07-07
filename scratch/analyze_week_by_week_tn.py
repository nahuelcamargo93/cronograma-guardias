import sqlite3
from datetime import date, timedelta
import sys
sys.path.append('.')
from restricciones.hard._utils import determinar_familia_ganadora

conn = sqlite3.connect('cronograma_inteligente.db')
c = conn.cursor()

c.execute("SELECT nombre FROM personal WHERE servicio_id = 2 AND COALESCE(activo, 1) = 1")
employees = [r[0] for r in c.fetchall()]

c.execute("SELECT nombre, fecha, turno, horas FROM guardias WHERE cronograma_id IN (583, 610)")
guardias = c.fetchall()

guardias_by_emp = {}
for name, fecha, turno, horas in guardias:
    guardias_by_emp.setdefault(name, []).append({'fecha': fecha, 'turno': turno, 'horas': horas})

# Let's check week-by-week categories in August
august_weeks = ['2026-07-27', '2026-08-03', '2026-08-10', '2026-08-17', '2026-08-24', '2026-08-31']
all_weeks = [
    '2026-07-06', '2026-07-13', '2026-07-20', # July
    '2026-07-27', '2026-08-03', '2026-08-10', '2026-08-17', '2026-08-24', '2026-08-31' # Aug/transition
]

# Map out categories for all weeks for all employees
cats = {name: {} for name in employees}
for name in employees:
    emp_guards = guardias_by_emp.get(name, [])
    for w in all_weeks:
        w_dt = date.fromisoformat(w)
        cat = determinar_familia_ganadora(emp_guards, w_dt)
        cats[name][w] = cat

print("=== DISPONIBILIDAD SEMANA A SEMANA EN AGOSTO ===")
d_min = 3

for fam in ['N', 'TN']:
    print(f"\n--- Turno {fam} ---")
    # For each week in August (excluding the historical weeks before July 27)
    # The week of July 27 is the first week of the August block (Aug 1 and Aug 2 are in it)
    for idx, w_target in enumerate(august_weeks):
        # The 3 weeks before w_target
        target_idx = all_weeks.index(w_target)
        prev_3_weeks = all_weeks[target_idx - d_min : target_idx]
        
        # Check how many worked 'fam' in those prev 3 weeks
        worked_recently = 0
        assigned_in_target = 0
        available_clean = 0
        
        for name in employees:
            has_worked = False
            for pw in prev_3_weeks:
                if cats[name][pw] == fam:
                    has_worked = True
                    break
            
            if has_worked:
                worked_recently += 1
            else:
                available_clean += 1
                
            if cats[name][w_target] == fam:
                assigned_in_target += 1
                
        min_needed = 49 / 5 # approx 10 people
        print(f"Semana {w_target}:")
        print(f"  Trabajaron {fam} recientemente (bloqueados): {worked_recently}")
        print(f"  Disponibles limpios: {available_clean} (capacidad turnos: {available_clean * 5})")
        print(f"  Asignados reales: {assigned_in_target} (turnos: {assigned_in_target * 5})")
        if available_clean < min_needed:
            print(f"  >> ¡AGOTAMIENTO DE CAPACIDAD! Faltan personas limpias para cubrir la demanda sin violar la regla.")

conn.close()
