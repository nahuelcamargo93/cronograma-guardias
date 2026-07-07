import sqlite3
from datetime import date, timedelta
import sys
sys.path.append('.')
from restricciones.hard._utils import determinar_familia_ganadora

conn = sqlite3.connect('cronograma_inteligente.db')
c = conn.cursor()

# Get all service 2 employees
c.execute("SELECT nombre FROM personal WHERE servicio_id = 2 AND COALESCE(activo, 1) = 1")
employees = [r[0] for r in c.fetchall()]

# Load all July guardias (583) and licenses in August
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
            # Check overlap
            if not (le < start or ls > end):
                return True
    return False

weeks = {
    '2026-07-27': {
        'prev': ['2026-07-06', '2026-07-13', '2026-07-20'],
        'start': '2026-07-27',
        'end': '2026-08-02'
    },
    '2026-08-03': {
        'prev': ['2026-07-13', '2026-07-20', '2026-07-27'],
        'start': '2026-08-03',
        'end': '2026-08-09'
    }
}

for w_key, info in weeks.items():
    print(f"\n================ SEMANA DEL {info['start']} al {info['end']} ================")
    
    for fam in ['N', 'TN']:
        print(f"\n--- Turno {fam} ---")
        blocked_names = []
        clean_names = []
        clean_but_licensed = []
        clean_and_available = []
        
        for name in employees:
            emp_guards = guardias_by_emp.get(name, [])
            worked_recently = False
            for pw in info['prev']:
                pw_dt = date.fromisoformat(pw)
                cat = determinar_familia_ganadora(emp_guards, pw_dt)
                if cat == fam:
                    worked_recently = True
                    break
            
            if worked_recently:
                blocked_names.append(name)
            else:
                clean_names.append(name)
                if is_on_license(name, info['start'], info['end']):
                    clean_but_licensed.append(name)
                else:
                    clean_and_available.append(name)
                    
        print(f"Total empleados: {len(employees)}")
        print(f"Bloqueados (hicieron {fam} en las 3 semanas previas): {len(blocked_names)}")
        print(f"Limpios teoricos: {len(clean_names)}")
        print(f"Limpios que tienen licencia en esta semana: {len(clean_but_licensed)} {clean_but_licensed if clean_but_licensed else ''}")
        print(f"-> DISPONIBLES REALES Y LIMPIOS: {len(clean_and_available)}")
        
        # Calculate theoretical capacity (assuming 5 shifts max per employee per week under Esquema Semanal)
        max_capacity_shifts = len(clean_and_available) * 5
        print(f"Capacidad maxima de turnos {fam} que pueden cubrir: {max_capacity_shifts}")
        
        if w_key == '2026-07-27':
            demanda_semanal = 14
        else:
            demanda_semanal = 49
            
        print(f"Demanda de turnos {fam} en la semana: {demanda_semanal}")
        
        if max_capacity_shifts < demanda_semanal:
            print(f"[FAIL] INVIABLE! Faltan cubrir {demanda_semanal - max_capacity_shifts} turnos de {fam}.")
        else:
            print("[OK] Capacidad teorica suficiente.")

conn.close()
