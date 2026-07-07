import sqlite3
import datetime
from datetime import date, timedelta

db_path = "c:\\Users\\asus\\Desktop\\Ryoko\\cronograma_inteligente\\cronograma_inteligente.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Cargar empleados del servicio 3
rows_emp = cursor.execute("""
    SELECT nombre, rol
    FROM personal
    WHERE servicio_id = 3 AND COALESCE(activo, 1) = 1
""").fetchall()

# Cargar turnos config del servicio 3
rows_turnos = cursor.execute("""
    SELECT tc.nombre, tc.dias_semana, p.nombre
    FROM turnos_config tc
    LEFT JOIN puestos p ON tc.puesto_id = p.id
    WHERE tc.servicio_id = 3 AND tc.activo = 1
""").fetchall()

turnos_dict = {r[0]: {'dias_semana': r[1], 'puesto': r[2]} for r in rows_turnos}

# Cargar asignaciones fijas eventuales en el rango
fecha_inicio = "2026-07-01"
fecha_fin = "2026-07-31"
lock_fecha_inicio = "2026-07-07"
lock_fecha_fin = "2026-07-13"

lock_ini_dt = date.fromisoformat(lock_fecha_inicio)
lock_fin_dt = date.fromisoformat(lock_fecha_fin)
fecha_inicio_dt_d = date.fromisoformat(fecha_inicio)

rows_ae = cursor.execute("""
    SELECT personal_nombre, fecha, turno
    FROM personal_asignaciones_fijas
    WHERE servicio_id = 3 AND activo = 1 AND fecha BETWEEN ? AND ?
""", (lock_fecha_inicio, lock_fecha_fin)).fetchall()

asignaciones_fijas_eventuales = {(r[0], r[1]): r[2].replace(" ", "_") for r in rows_ae}

# Mapear guardias_base_indexadas
guardias_base_indexadas = set()
for (nombre_ae, fecha_ae), turno_ae in asignaciones_fijas_eventuales.items():
    ae_dt = date.fromisoformat(fecha_ae)
    dia_idx = (ae_dt - fecha_inicio_dt_d).days
    guardias_base_indexadas.add((nombre_ae, dia_idx, turno_ae))

print("=== GUARDIAS BASE INDEXADAS ===")
for g in sorted(guardias_base_indexadas, key=lambda x: (x[1], x[0])):
    print(f"Dia {g[1]} ({fecha_inicio_dt_d + timedelta(days=g[1])}): {g[0]} -> {g[2]}")

print("\n=== EVALUANDO FORZADOS POR DIA EN RANGO BLOQUEADO ===")
for dia in range(31):
    fecha_actual_d = fecha_inicio_dt_d + timedelta(days=dia)
    if not (lock_ini_dt <= fecha_actual_d <= lock_fin_dt):
        continue
    
    print(f"\nFecha: {fecha_actual_d.isoformat()} (Dia idx: {dia})")
    
    # Demanda minima requerida por dia
    # Lunes a Viernes es Semana, Sabado/Domingo y Feriados es Finde_Feriado
    # Feriados: 9 y 10
    es_feriado = fecha_actual_d.isoformat() in ["2026-07-09", "2026-07-10"]
    es_finde = fecha_actual_d.weekday() >= 5 or es_feriado
    tipo_dia = "Finde_Feriado" if es_finde else "Semana"
    
    planta_min = 3
    residente_min = 1
    
    print(f"Tipo dia: {tipo_dia} | Demandas Min: Planta={planta_min}, Residente={residente_min}")
    
    asignados_planta_dia = []
    asignados_planta_noche = []
    asignados_residente_dia = []
    asignados_residente_noche = []
    
    for emp_nom, emp_rol in rows_emp:
        # Qué turnos se le forzarían a 1 a este empleado hoy?
        for t_nom, t_info in turnos_dict.items():
            # Filtro simplificado de main.py
            # dias habilitados
            dias_permitidos = {int(x) for x in t_info['dias_semana'].split(",")}
            if es_finde:
                if not (5 in dias_permitidos or 6 in dias_permitidos):
                    continue
            else:
                if fecha_actual_d.weekday() not in dias_permitidos:
                    continue
            
            # Puestos habilitados/rol
            if emp_rol != t_info['puesto']:
                continue
            
            # Verificar si está asignado
            es_asignado = False
            for (n_g, d_g, t_g) in guardias_base_indexadas:
                if n_g == emp_nom and d_g == dia:
                    if t_nom == t_g or t_nom.startswith(t_g + "_") or t_g.startswith(t_nom + "_"):
                        es_asignado = True
                        break
            
            if es_asignado:
                print(f"  [FORZADO A 1] {emp_nom} ({emp_rol}) -> {t_nom}")
                if t_info['puesto'] == 'Planta':
                    if "Dia" in t_nom or "Guardia" in t_nom:
                        asignados_planta_dia.append(emp_nom)
                    if "Noche" in t_nom or "Guardia" in t_nom:
                        asignados_planta_noche.append(emp_nom)
                elif t_info['puesto'] == 'Residente':
                    if "Dia" in t_nom or "Guardia" in t_nom:
                        asignados_residente_dia.append(emp_nom)
                    if "Noche" in t_nom or "Guardia" in t_nom:
                        asignados_residente_noche.append(emp_nom)
                        
    print(f"  --> Planta Dia: {len(asignados_planta_dia)} ({', '.join(asignados_planta_dia)})")
    print(f"  --> Planta Noche: {len(asignados_planta_noche)} ({', '.join(asignados_planta_noche)})")
    print(f"  --> Residente Dia: {len(asignados_residente_dia)} ({', '.join(asignados_residente_dia)})")
    print(f"  --> Residente Noche: {len(asignados_residente_noche)} ({', '.join(asignados_residente_noche)})")

conn.close()
