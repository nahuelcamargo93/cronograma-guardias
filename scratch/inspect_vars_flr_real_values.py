import sqlite3
import pandas as pd
import datetime
from datetime import date, timedelta
from ortools.sat.python import cp_model

from database import queries as db_queries
from database.data_loader import obtener_empleados, obtener_turnos
from main import construir_modelo
from restricciones.hard._utils import is_finde

servicio_id = 2
fecha_inicio = "2026-08-01"
fecha_fin = "2026-08-31"

fecha_inicio_dt = date.fromisoformat(fecha_inicio)
fecha_fin_dt = date.fromisoformat(fecha_fin)
dias_del_bloque = (fecha_fin_dt - fecha_inicio_dt).days + 1

lunes_unicos = set()
for d in range(dias_del_bloque):
    fecha_d = fecha_inicio_dt + timedelta(days=d)
    lunes = fecha_d - timedelta(days=fecha_d.weekday())
    lunes_unicos.add(lunes)
num_semanas = len(lunes_unicos)

feriados_indices = []
feriados_db = db_queries.obtener_feriados(fecha_inicio, fecha_fin, servicio_id=servicio_id)
for f_str in feriados_db:
    f_dt = date.fromisoformat(f_str)
    delta = (f_dt - fecha_inicio_dt).days
    if 0 <= delta < dias_del_bloque:
        feriados_indices.append(delta)

config_turnos, turnos_info, demanda_req, ajustes_db = db_queries.cargar_configuracion_turnos(
    servicio_id=servicio_id, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin
)
reglas_servicio = db_queries.cargar_reglas_servicio(servicio_id)
ajustes_reglas = db_queries.cargar_ajustes_reglas_personal(fecha_inicio, fecha_fin)
ajustes_servicio = db_queries.cargar_ajustes_reglas_servicio(fecha_inicio, fecha_fin, servicio_id)
ajustes_reglas['__servicio__'] = ajustes_servicio

empleados = obtener_empleados(servicio_id, fecha_inicio, dias_del_bloque)
turnos_dict = obtener_turnos(servicio_id)
historial_semana_previa = db_queries.cargar_guardias_previas(fecha_inicio, dias_atras=28, servicio_id=servicio_id)

offset_dia = fecha_inicio_dt.weekday()

modelo, turnos, flr_tracker, ctx = construir_modelo(
    empleados, config_turnos, turnos_dict, demanda_req, ajustes_db,
    dias_del_bloque, feriados_indices, offset_dia, num_semanas,
    reglas_servicio=reglas_servicio,
    ajustes_reglas_personal=ajustes_reglas,
    historial_semana_previa=historial_semana_previa,
    servicio_id=servicio_id,
    fecha_inicio=fecha_inicio,
    fecha_fin=fecha_fin,
    modo_debug=False,
    force_assumptions=False
)

solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 15
status = solver.Solve(modelo)

print(f"Estado de resolucion: {solver.StatusName(status)}")

target_emp_name = "ANDREOLI LUCIANA"
emp_obj = next(e for e in empleados if e.nombre == target_emp_name)

if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    print(f"\n=== Analisis de Opciones FLR para {target_emp_name} ===")
    
    # Vamos a replicar el loop de findes
    findes_raw = {}
    for d in range(dias_del_bloque):
        wd = (fecha_inicio_dt + timedelta(days=d)).weekday()
        if wd in (5, 6):
            fd = fecha_inicio_dt + timedelta(days=d)
            lunes = (fd - timedelta(days=wd)).isoformat()
            findes_raw.setdefault(lunes, []).append((d, wd))

    findes = {
        lunes: dias_f for lunes, dias_f in findes_raw.items()
        if any(w == 5 for _, w in dias_f) and any(w == 6 for _, w in dias_f)
    }

    for lunes, dias_f in findes.items():
        d_sat = next((d for d, w in dias_f if w == 5), None)
        print(f"\nSemana lunes {lunes}:")
        
        # Evaluar las 3 opciones
        flr_offsets = {"jd": -2, "vl": -1, "sm": 0}
        for pref, offset in flr_offsets.items():
            d_inicio = d_sat + offset
            dias_flr = [d_inicio, d_inicio + 1, d_inicio + 2, d_inicio + 3]
            
            # Ver si existe en flr_tracker
            # flr_tracker se llena usando d_sat - 2, d_sat - 1, d_sat como d
            tracker_key = (target_emp_name, d_inicio)
            if tracker_key in flr_tracker:
                var = flr_tracker[tracker_key]
                val = solver.Value(var)
                
                # Obtener variables de turnos asociadas a este bloque
                vars_bloque_flr = []
                for d_e in dias_flr:
                    if d_e < 0 or d_e >= dias_del_bloque:
                        continue
                    es_f = is_finde(d_e, offset_dia, feriados_indices)
                    for t in config_turnos.get("Finde_Feriado" if es_f else "Semana", {}).keys():
                        if (target_emp_name, d_e, t) in turnos:
                            vars_bloque_flr.append(((d_e, t), turnos[(target_emp_name, d_e, t)]))
                
                turnos_asignados_bloque = []
                for (d_e, t), t_var in vars_bloque_flr:
                    if solver.Value(t_var) == 1:
                        turnos_asignados_bloque.append(f"dia {d_e} ({t})")
                
                print(f"  Opcion {pref} (d_inicio={d_inicio}): value={val}, vars_count={len(vars_bloque_flr)}, turnos_asignados={turnos_asignados_bloque}")
            else:
                print(f"  Opcion {pref} (d_inicio={d_inicio}): No creada (None)")
else:
    print("Modelo no resuelto")
conn.close()
