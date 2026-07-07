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

c.execute("""
    SELECT nombre, fecha_inicio, fecha_fin 
    FROM licencias 
    WHERE COALESCE(activa, 1) = 1 AND nombre IN (SELECT nombre FROM personal WHERE servicio_id = 2)
""")
licencias = c.fetchall()

def is_on_license(nombre, start_date, end_date):
    start = date.fromisoformat(start_date)
    end = date.fromisoformat(end_date)
    for name, l_start, l_end in licencias:
        if name == nombre:
            ls = date.fromisoformat(l_start)
            le = date.fromisoformat(l_end)
            if not (le < start or ls > end):
                return True
    return False

# Let's check for TN
print("=== ANÁLISIS TN SEMANA A SEMANA CON LICENCIAS ===")

# July weeks
# 2026-07-06, 2026-07-13, 2026-07-20
# August weeks
aug_weeks = [
    ('2026-07-27', '2026-08-02'),
    ('2026-08-03', '2026-08-09'),
    ('2026-08-10', '2026-08-16'),
    ('2026-08-17', '2026-08-23'),
    ('2026-08-24', '2026-08-30'),
    ('2026-08-31', '2026-08-31')
]

# We need to simulate the solver's assignments for TN
# In each week, we need to assign at least 10 people to TN (each can do max 5 shifts, to cover 49 demand).
# Let's track who worked TN.
# Initialize with history from July
worked_tn = {}
for name in employees:
    worked_tn[name] = {}
    emp_guards = guardias_by_emp.get(name, [])
    # July weeks
    for w in ['2026-07-06', '2026-07-13', '2026-07-20']:
        w_dt = date.fromisoformat(w)
        cat = determinar_familia_ganadora(emp_guards, w_dt)
        worked_tn[name][w] = (cat == 'TN')

# Now run week-by-week
all_weeks_keys = ['2026-07-06', '2026-07-13', '2026-07-20']

for w_start, w_end in aug_weeks:
    all_weeks_keys.append(w_start)
    
    # Who is blocked?
    blocked_count = 0
    clean_and_avail = []
    
    # The 3 weeks before w_start
    prev_3 = all_weeks_keys[-4:-1]
    
    for name in employees:
        recently = False
        for pw in prev_3:
            if worked_tn[name].get(pw, False):
                recently = True
                break
        if recently:
            blocked_count += 1
        else:
            # Check license
            if not is_on_license(name, w_start, w_end):
                clean_and_avail.append(name)
                
    print(f"Semana {w_start}:")
    print(f"  Bloqueados por historia reciente: {blocked_count}")
    print(f"  Disponibles limpios y sin licencia: {len(clean_and_avail)}")
    
    # We must assign at least 10 people to TN for this week.
    # We choose the first 10 from clean_and_avail.
    if len(clean_and_avail) < 10:
        print(f"  [FAIL] ¡IMPOSIBLE! Faltan {10 - len(clean_and_avail)} personas para cubrir la demanda sin violar la regla.")
        # As fallback we assign as many as we can
        assigned_count = len(clean_and_avail)
    else:
        assigned_count = 10
        
    for name in employees:
        worked_tn[name][w_start] = False
    for name in clean_and_avail[:assigned_count]:
        worked_tn[name][w_start] = True
        
    print(f"  Asignados a TN: {assigned_count}")

conn.close()
