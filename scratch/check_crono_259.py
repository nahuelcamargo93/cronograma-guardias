import sqlite3
from datetime import date, timedelta

db_path = "cronograma_inteligente.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

crono_id = 259

# Obtener guardias del cronograma 259
cursor.execute("""
    SELECT nombre, fecha, turno 
    FROM guardias 
    WHERE cronograma_id = ?
""", (crono_id,))
rows = cursor.fetchall()

# Organizar por nombre y semana
guardias_por_emp_sem = {}
for nombre, fecha_str, turno in rows:
    fecha = date.fromisoformat(fecha_str)
    lunes = fecha - timedelta(days=fecha.weekday())
    sem_key = lunes.isoformat()
    
    guardias_por_emp_sem.setdefault(nombre, {}).setdefault(sem_key, []).append(turno)

# Validar regla mezcla_semanal_dura
infracciones = 0
for nombre, semanas in guardias_por_emp_sem.items():
    for sem_key, turnos in semanas.items():
        # Clasificar turnos en familias
        familias_activas = set()
        for t in turnos:
            if t == 'M': familias_active = 'M'
            elif t == 'T': familias_active = 'T'
            elif t == 'TN': familias_active = 'TN'
            elif t == 'N': familias_active = 'N'
            elif t == 'MT':
                # MT es compatible con M o T. Si se mezcla con M y T, ya de por sí no debería mezclar con TN o N
                familias_active = 'MT'
            elif t == 'TNN':
                familias_active = 'TNN'
            else:
                familias_active = None
                
            if familias_active:
                familias_activas.add(familias_active)
        
        # Verificar incompatibilidades: no puede mezclar M/T/MT con TN/N/TNN
        grupo_dia = familias_activas.intersection({'M', 'T', 'MT'})
        grupo_noche = familias_activas.intersection({'TN', 'N', 'TNN'})
        
        # Además, M y T no pueden mezclarse en la misma semana
        if 'M' in familias_activas and 'T' in familias_activas:
            print(f"[VIOLACION] {nombre} tiene M y T en la semana {sem_key}: {turnos}")
            infracciones += 1
            
        if grupo_dia and grupo_noche:
            print(f"[VIOLACION] {nombre} mezcla DIA y NOCHE en la semana {sem_key}: {turnos}")
            infracciones += 1

if infracciones == 0:
    print("¡ÉXITO! No se detectaron violaciones a la regla de mezcla semanal en el cronograma 259.")
else:
    print(f"Se detectaron {infracciones} violaciones.")

conn.close()
