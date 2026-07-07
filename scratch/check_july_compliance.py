import sqlite3
from datetime import date, timedelta
import sys
sys.path.append('.')
from restricciones.hard._utils import determinar_familia_ganadora, mapear_turno_a_familias

conn = sqlite3.connect('cronograma_inteligente.db')
c = conn.cursor()

c.execute("SELECT nombre FROM personal WHERE servicio_id = 2 AND COALESCE(activo, 1) = 1")
employees = [r[0] for r in c.fetchall()]

c.execute("SELECT nombre, fecha, turno, horas FROM guardias WHERE cronograma_id = 583")
guardias = c.fetchall()

guardias_by_emp = {}
for name, fecha, turno, horas in guardias:
    guardias_by_emp.setdefault(name, []).append({'fecha': fecha, 'turno': turno, 'horas': horas})

july_weeks = ['2026-07-06', '2026-07-13', '2026-07-20', '2026-07-27']

print("=== VERIFICACIÓN DE REGLAS EN JULIO (CRONOGRAMA 583) ===")

viol_esquema = 0
viol_mezcla = 0
total_weeks_checked = 0

for name in sorted(employees):
    emp_guards = guardias_by_emp.get(name, [])
    for w in july_weeks:
        w_dt = date.fromisoformat(w)
        # Get guardias of this week
        week_guards = [g for g in emp_guards if w_dt <= date.fromisoformat(g['fecha']) < w_dt + timedelta(days=7)]
        if not week_guards:
            continue
            
        total_weeks_checked += 1
        
        # 1. Check ESQUEMA_SEMANAL_ENFERMERIA
        # Exactly 1 shift of 12h (MT or TNN) and 4 shifts of 6h (M, T, TN, N)
        shifts_12h = [g for g in week_guards if g['horas'] == 12]
        shifts_6h = [g for g in week_guards if g['horas'] == 6]
        
        if len(shifts_12h) != 1 or len(shifts_6h) != 4:
            viol_esquema += 1
            if viol_esquema <= 5:
                print(f"Violación esquema: {name} en semana {w}")
                print(f"  12h shifts ({len(shifts_12h)}): {[g['turno'] for g in shifts_12h]}")
                print(f"  6h shifts ({len(shifts_6h)}): {[g['turno'] for g in shifts_6h]}")
                
        # 2. Check MEZCLA_SEMANAL_DURA
        # Only one family of turns in the week
        families = set()
        for g in week_guards:
            families.update(mapear_turno_a_familias(g['turno']))
        if len(families) > 1:
            viol_mezcla += 1
            if viol_mezcla <= 5:
                print(f"Violación mezcla: {name} en semana {w}")
                print(f"  Familias encontradas: {list(families)} (turnos: {[g['turno'] for g in week_guards]})")

print(f"\nResumen:")
print(f"Total semanas analizadas: {total_weeks_checked}")
print(f"Total violaciones ESQUEMA_SEMANAL_ENFERMERIA: {viol_esquema}")
print(f"Total violaciones MEZCLA_SEMANAL_DURA: {viol_mezcla}")

conn.close()
