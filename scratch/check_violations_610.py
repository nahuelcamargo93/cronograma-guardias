import sqlite3
from datetime import date, timedelta
import sys
sys.path.append('.')
from restricciones.hard._utils import determinar_familia_ganadora, mapear_turno_a_familias

conn = sqlite3.connect('cronograma_inteligente.db')
c = conn.cursor()

c.execute("SELECT nombre FROM personal WHERE servicio_id = 2 AND COALESCE(activo, 1) = 1")
employees = [r[0] for r in c.fetchall()]

c.execute("""
    SELECT nombre, fecha, turno, horas 
    FROM guardias 
    WHERE cronograma_id IN (583, 610)
""")
guardias_raw = c.fetchall()

guardias_by_emp = {}
for name, fecha, turno, horas in guardias_raw:
    guardias_by_emp.setdefault(name, []).append({
        'fecha': fecha,
        'turno': turno,
        'horas': horas
    })

c.execute("""
    SELECT nombre, fecha_lunes, categoria 
    FROM semanas_categorias 
    WHERE cronograma_id = 610
""")
semanas_cat_db = {}
for name, fecha_lunes, cat in c.fetchall():
    semanas_cat_db.setdefault(name, {})[fecha_lunes] = cat

semanas_keys = [
    '2026-07-06', '2026-07-13', '2026-07-20',
    '2026-07-27', '2026-08-03', '2026-08-10', '2026-08-17', '2026-08-24', '2026-08-31'
]

d_min = 3
w = d_min + 1

violations_n = []
violations_tn = []

for name in sorted(employees):
    emp_guardias = guardias_by_emp.get(name, [])
    
    # Computed from actual guardias
    cats_computed = []
    for sem_str in semanas_keys:
        sem_dt = date.fromisoformat(sem_str)
        cat = determinar_familia_ganadora(emp_guardias, sem_dt)
        cats_computed.append(cat)
        
    # Loaded from semanas_categorias (where available) otherwise computed
    cats_db = []
    for sem_str in semanas_keys:
        if sem_str in ('2026-07-06', '2026-07-13', '2026-07-20'):
            sem_dt = date.fromisoformat(sem_str)
            cat = determinar_familia_ganadora(emp_guardias, sem_dt)
            cats_db.append(cat)
        else:
            cat = semanas_cat_db.get(name, {}).get(sem_str, None)
            cats_db.append(cat)
            
    for fam, violations_list in [('N', violations_n), ('TN', violations_tn)]:
        seq_comp = [1 if c == fam else 0 for c in cats_computed]
        seq_db = [1 if c == fam else 0 for c in cats_db]
        
        for i in range(len(seq_comp) - w + 1):
            window = seq_comp[i:i+w]
            if sum(window) > 1:
                active_weeks = [semanas_keys[i + idx] for idx, val in enumerate(window) if val == 1]
                violations_list.append({
                    'empleado': name,
                    'tipo': 'computed',
                    'window_start': semanas_keys[i],
                    'weeks': active_weeks,
                    'sequence': seq_comp[i:i+w]
                })
                
        for i in range(len(seq_db) - w + 1):
            window = seq_db[i:i+w]
            if sum(window) > 1:
                active_weeks = [semanas_keys[i + idx] for idx, val in enumerate(window) if val == 1]
                violations_list.append({
                    'empleado': name,
                    'tipo': 'db',
                    'window_start': semanas_keys[i],
                    'weeks': active_weeks,
                    'sequence': seq_db[i:i+w]
                })

# Deduplicate
def get_deduped(violations):
    seen = set()
    result = []
    for v in violations:
        key = (v['empleado'], tuple(v['weeks']))
        if key not in seen:
            seen.add(key)
            result.append(v)
    return result

dedup_n = get_deduped(violations_n)
dedup_tn = get_deduped(violations_tn)

# Write full details to a report file
report_path = 'scratch/reporte_violaciones_610.txt'
with open(report_path, 'w', encoding='utf-8') as f:
    f.write("=== REPORTE DETALLADO DE INFRACCIONES - CRONOGRAMA 610 ===\n")
    f.write(f"Regla: DISTANCIA_MINIMA_TIPO_SEMANA (mínimo {d_min} semanas libres entre asignaciones)\n\n")
    
    f.write(f"--- TURNO NOCHE (N) (Total violaciones: {len(dedup_n)}) ---\n")
    for v in dedup_n:
        f.write(f"Empleado: {v['empleado']}\n")
        f.write(f"  Semanas detectadas con N: {v['weeks']}\n")
        f.write(f"  Ventana: {v['window_start']} -> secuencia: {v['sequence']}\n")
        f.write(f"  Tipo de detección: {v['tipo']}\n\n")
        
    f.write(f"\n--- TARDE NOCHE (TN) (Total violaciones: {len(dedup_tn)}) ---\n")
    for v in dedup_tn:
        f.write(f"Empleado: {v['empleado']}\n")
        f.write(f"  Semanas detectadas con TN: {v['weeks']}\n")
        f.write(f"  Ventana: {v['window_start']} -> secuencia: {v['sequence']}\n")
        f.write(f"  Tipo de detección: {v['tipo']}\n\n")

# Print short summary to console
print(f"Cálculo completado. Reporte escrito en {report_path}")
print(f"Total infracciones de tipo N (Noche): {len(dedup_n)}")
print(f"Total infracciones de tipo TN (Tarde Noche): {len(dedup_tn)}")

print("\n--- EJEMPLOS / RESUMEN N (Noche) ---")
if not dedup_n:
    print("¡No se encontraron violaciones para N (Noche)!")
else:
    for v in dedup_n[:10]:
        print(f"- {v['empleado']}: semanas {v['weeks']}")
    if len(dedup_n) > 10:
        print(f"... y {len(dedup_n) - 10} más.")

print("\n--- EJEMPLOS / RESUMEN TN (Tarde Noche) ---")
if not dedup_tn:
    print("¡No se encontraron violaciones para TN (Tarde Noche)!")
else:
    for v in dedup_tn[:15]:
        print(f"- {v['empleado']}: semanas {v['weeks']}")
    if len(dedup_tn) > 15:
        print(f"... y {len(dedup_tn) - 15} más.")

conn.close()
