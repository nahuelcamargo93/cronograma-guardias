import sys
sys.path.append(".")
import datetime
from datetime import date, timedelta
from database import queries as db_queries
from database.data_loader import obtener_empleados, obtener_turnos
from utils import time_to_float
import rule_engine as _re

servicio_id = 1
fecha_inicio = "2026-06-22"
fecha_fin = "2026-07-31"

db_queries.init_licencias(servicio_id)
fecha_inicio_dt = datetime.datetime.strptime(fecha_inicio, "%Y-%m-%d")
fecha_fin_dt    = datetime.datetime.strptime(fecha_fin,    "%Y-%m-%d")
total_dias = (fecha_fin_dt - fecha_inicio_dt).days + 1
DIAS_DEL_BLOQUE = total_dias

config_turnos, turnos_dict_raw, demanda_req, ajustes_db = db_queries.cargar_configuracion_turnos(
    servicio_id=servicio_id, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin
)
reglas_servicio_db = db_queries.cargar_reglas_servicio(servicio_id)
ajustes_reglas = db_queries.cargar_ajustes_reglas_personal(fecha_inicio, fecha_fin)

empleados = obtener_empleados(servicio_id, fecha_inicio, DIAS_DEL_BLOQUE)
turnos_dict = obtener_turnos(servicio_id)
historial_semana_previa = db_queries.cargar_guardias_previas(fecha_inicio, dias_atras=28, servicio_id=servicio_id)

print(f"Loaded {len(empleados)} employees and previous history for {len(historial_semana_previa)} employees.")

# Let's inspect historical records for our target people
target_names = ['Leonforte, Franco', 'Guardia, Gabriel', 'Flores, Franco', 'Sosa, Nicolas']
for name in target_names:
    print(f"\nHistory for {name}:")
    for g in historial_semana_previa.get(name, []):
        print(f"  {g}")

print("\n--- Simulating descanso check with previous guardias ---")
fecha_inicio_dt_d = date.fromisoformat(fecha_inicio)
violations_found = []

for emp in empleados:
    hist_prev = historial_semana_previa.get(emp.nombre, [])
    for p in hist_prev:
        fecha_prev = date.fromisoformat(p['fecha'])
        T_prev = p['turno']
        
        # Resolve rules for the previous date
        params_prev = _re.resolver_parametros_regla(
            'DESCANSO_ENTRE_TURNOS', emp.nombre, fecha_prev.isoformat(),
            reglas_servicio_db, emp.reglas, ajustes_reglas
        )
        if not _re.regla_existe(params_prev) or _re.regla_suspendida(params_prev):
            continue
        
        descansos_por_turno_prev = {}
        horas_global_prev = 12
        if isinstance(params_prev, dict):
            descansos_por_turno_prev = params_prev.get('por_turno', {})
            horas_global_prev = params_prev.get('horas', 12)
            
        R_prev = descansos_por_turno_prev.get(T_prev, horas_global_prev)
        if R_prev <= 0:
            continue
            
        t_info_prev = turnos_dict.get(T_prev.replace(" ", "_"))
        if t_info_prev:
            H_start_prev = time_to_float(t_info_prev.hora_inicio)
        else:
            if "Noche" in T_prev: H_start_prev = 20.0
            elif "Tarde" in T_prev: H_start_prev = 14.0
            else: H_start_prev = 8.0
            
        D_prev = p.get('horas', 12)
        H_fin_prev = H_start_prev + D_prev
        
        # Look forward at days d2 of current schedule
        # max days to look forward is based on when the rest requirement expires
        max_d2_to_check = int((H_fin_prev + R_prev) // 24) + 1
        
        for d2 in range(min(DIAS_DEL_BLOQUE, max_d2_to_check)):
            fecha_d2 = fecha_inicio_dt_d + timedelta(days=d2)
            d_diff = (fecha_d2 - fecha_prev).days
            if d_diff < 0:
                continue
                
            td2 = "Finde_Feriado" if ((d2 + fecha_inicio_dt.weekday()) % 7 >= 5) else "Semana"
            for T2 in config_turnos.get(td2, {}).keys():
                info_T2 = turnos_dict.get(T2)
                if not info_T2:
                    continue
                H_start_T2 = time_to_float(info_T2.hora_inicio)
                
                descanso_real = d_diff * 24 + H_start_T2 - H_fin_prev
                if descanso_real < R_prev:
                    violations_found.append({
                        'nombre': emp.nombre,
                        'fecha_prev': fecha_prev.isoformat(),
                        'turno_prev': T_prev,
                        'R_prev': R_prev,
                        'd2': d2,
                        'fecha_d2': fecha_d2.isoformat(),
                        'turno_curr': T2,
                        'descanso_real': descanso_real
                    })

print(f"Total simulated violations with previous history: {len(violations_found)}")
for v in violations_found:
    print(f"Emp: {v['nombre']} | Prev: {v['fecha_prev']} {v['turno_prev']} (rest: {v['R_prev']}h) | Curr: {v['fecha_d2']} {v['turno_curr']} | Rest actual: {v['descanso_real']}h -> VIOLATION")
