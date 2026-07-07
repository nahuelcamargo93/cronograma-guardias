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

# Initialize history for N and TN
worked_n = {}
worked_tn = {}
july_weeks = ['2026-07-06', '2026-07-13', '2026-07-20']

for name in employees:
    worked_n[name] = {}
    worked_tn[name] = {}
    emp_guards = guardias_by_emp.get(name, [])
    for w in july_weeks:
        w_dt = date.fromisoformat(w)
        cat = determinar_familia_ganadora(emp_guards, w_dt)
        worked_n[name][w] = (cat == 'N')
        worked_tn[name][w] = (cat == 'TN')

aug_weeks = [
    ('2026-07-27', '2026-08-02'),
    ('2026-08-03', '2026-08-09'),
    ('2026-08-10', '2026-08-16'),
    ('2026-08-17', '2026-08-23'),
    ('2026-08-24', '2026-08-30'),
    ('2026-08-31', '2026-08-31')
]

all_weeks_keys = ['2026-07-06', '2026-07-13', '2026-07-20']

# We need E_TN >= 10 and E_N >= 8 in each week.
# We will use simple backtracking to see if a valid sequence of assignments exists!
def simulate_joint(week_idx):
    if week_idx >= len(aug_weeks):
        return True # Found a valid sequence!
        
    w_start, w_end = aug_weeks[week_idx]
    all_weeks_keys.append(w_start)
    
    # Calculate available clean pools
    prev_3 = all_weeks_keys[-4:-1]
    
    clean_n = []
    clean_tn = []
    
    for name in employees:
        if is_on_license(name, w_start, w_end):
            continue
            
        recent_n = any(worked_n[name].get(pw, False) for pw in prev_3)
        recent_tn = any(worked_tn[name].get(pw, False) for pw in prev_3)
        
        if not recent_n:
            clean_n.append(name)
        if not recent_tn:
            clean_tn.append(name)
            
    # Try all combinations of E_TN (10 employees) from clean_tn and E_N (8 employees) from clean_n
    # such that they are disjoint.
    # To do this efficiently, we can use a quick heuristics check:
    # Is the union of clean_n and clean_tn large enough? We need at least 18 unique employees.
    union = set(clean_n) | set(clean_tn)
    if len(union) < 18 or len(clean_n) < 8 or len(clean_tn) < 10:
        # Failure! Clean pool is too small.
        all_weeks_keys.pop()
        return False
        
    # We can try to select the groups
    # To keep it fast, let's pick 10 disjoint from clean_tn, and 8 from clean_n.
    # We prioritize selecting clean_tn first, then clean_n.
    import itertools
    
    # Let's try to find at least one valid partition
    found = False
    for group_tn in itertools.combinations(clean_tn, 10):
        # Remaining clean_n elements that are not in group_tn
        rem_clean_n = [x for x in clean_n if x not in group_tn]
        if len(rem_clean_n) >= 8:
            group_n = rem_clean_n[:8]
            
            # Record these choices
            for name in employees:
                worked_tn[name][w_start] = (name in group_tn)
                worked_n[name][w_start] = (name in group_n)
                
            # Recurse
            if simulate_joint(week_idx + 1):
                return True
                
    all_weeks_keys.pop()
    return False

print("Ejecutando simulación de búsqueda con backtracking para N y TN...")
possible = simulate_joint(0)
if possible:
    print("[OK] ¡Es teóricamente posible encontrar una asignación de N y TN sin romper las reglas de distancia!")
else:
    print("[FAIL] ¡Inviable! No existe ninguna combinación de asignaciones que respete la distancia de N y TN en todas las semanas.")

conn.close()
