import sys
import os
sys.path.append(os.path.abspath("."))
import sqlite3
from datetime import datetime, date, timedelta
from ortools.sat.python import cp_model
from database.data_loader import obtener_empleados, obtener_turnos
from database import queries as db_queries
from data import FECHA_INICIO, FECHA_FIN, FERIADOS, SERVICIO_ID
import hard_rules
import rule_engine as _re

fecha_inicio = FECHA_INICIO
fecha_fin = FECHA_FIN
servicio_id = SERVICIO_ID

print(f"Diagnosing Servicio {servicio_id} from {fecha_inicio} to {fecha_fin}...")

fecha_inicio_dt = datetime.strptime(fecha_inicio, "%Y-%m-%d")
fecha_fin_dt = datetime.strptime(fecha_fin, "%Y-%m-%d")
total_dias = (fecha_fin_dt - fecha_inicio_dt).days + 1
num_semanas = (total_dias + 6) // 7

config_turnos, metadata_turnos_raw, demanda_req, ajustes_db = db_queries.cargar_configuracion_turnos(
    servicio_id=servicio_id, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin
)
reglas_servicio_db = db_queries.cargar_reglas_servicio(servicio_id)
ajustes_reglas = db_queries.cargar_ajustes_reglas_personal(fecha_inicio, fecha_fin)
empleados = obtener_empleados(servicio_id, fecha_inicio, total_dias)
turnos_dict = obtener_turnos(servicio_id)
historial_semana_previa = db_queries.cargar_guardias_previas(fecha_inicio, dias_atras=28, servicio_id=servicio_id)
offset_dia = fecha_inicio_dt.weekday()

feriados_indices = []
for f_str in FERIADOS:
    f_dt = datetime.strptime(f_str, "%Y-%m-%d")
    delta = (f_dt - fecha_inicio_dt).days
    if 0 <= delta < total_dias:
        feriados_indices.append(delta)

def custom_aplicar_cobertura_dinamica(modelo, turnos_vars, day_to_skip=None, shift_to_skip=None):
    from utils import time_to_float
    fecha_inicio_dt_d = date.fromisoformat(fecha_inicio)
    
    for dia in range(total_dias):
        if dia == day_to_skip:
            continue
            
        es_f = ((dia + offset_dia) % 7) >= 5 or dia in feriados_indices
        tipo_dia = "Finde_Feriado" if es_f else "Semana"
        fecha_actual_iso = (fecha_inicio_dt_d + timedelta(days=dia)).isoformat()
        dia_semana_actual = (dia + offset_dia) % 7
        
        candidates_by_window = {}
        for demanda in demanda_req.get(tipo_dia, []):
            dias_sem = demanda.get("dias_semana")
            applies = False
            if dias_sem:
                dias_validos = [int(x.strip()) for x in dias_sem.split(",") if x.strip().isdigit()]
                if dia_semana_actual in dias_validos:
                    applies = True
            else:
                if dia in feriados_indices:
                    applies = True
                elif tipo_dia == "Semana" and dia_semana_actual in [0, 1, 2, 3, 4]:
                    applies = True
                elif tipo_dia == "Finde_Feriado" and dia_semana_actual in [5, 6]:
                    applies = True
                    
            if applies:
                puesto_key = demanda.get("puesto_id")
                key = (puesto_key, demanda["hora_inicio"], demanda["hora_fin"])
                candidates_by_window.setdefault(key, []).append(demanda)
                
        final_demandas = []
        for key, candidates in candidates_by_window.items():
            especificas = [c for c in candidates if c.get("dias_semana")]
            if especificas:
                final_demandas.extend(especificas)
            else:
                final_demandas.extend(candidates)
                
        demandas_por_ventana = {}
        for demanda in final_demandas:
            key = (demanda["hora_inicio"], demanda["hora_fin"])
            demandas_por_ventana.setdefault(key, []).append(demanda)
            
        for (h_start, h_end), window_demands in demandas_por_ventana.items():
            if shift_to_skip == h_start:
                continue
                
            d_h_start = time_to_float(h_start)
            d_h_end = time_to_float(h_end)
            d_abs_start = dia * 24 + d_h_start
            if d_h_end <= d_h_start and not (d_h_start == 0 and d_h_end == 0):
                d_abs_end = (dia + 1) * 24 + d_h_end
            elif d_h_end == 0 and d_h_start > 0:
                d_abs_end = (dia + 1) * 24
            else:
                d_abs_end = dia * 24 + d_h_end
                
            for dem in window_demands:
                c_min = dem.get("cantidad_min")
                c_max = dem.get("cantidad_max")
                
                # Check for adjustments
                aj_o = None
                for (fi, ff), cambios in ajustes_db.items():
                    if fi <= fecha_actual_iso <= ff:
                        for adj in cambios:
                            if adj["demanda_config_id"] == dem["id"]:
                                aj_o = adj
                                break
                if aj_o:
                    if aj_o["dias_override"]:
                        dias_validos = [int(x) for x in aj_o["dias_override"].split(",")]
                        if dia_semana_actual in dias_validos or dia in feriados_indices:
                            c_min = aj_o.get("cantidad_min")
                            c_max = aj_o.get("cantidad_max")
                    else:
                        c_min = aj_o.get("cantidad_min")
                        c_max = aj_o.get("cantidad_max")
                        
                if c_min is None and c_max is None:
                    continue
                    
                pool_normales = []
                pool_extras = []
                has_block_vars = False
                
                for emp in empleados:
                    fecha_bloque = (fecha_inicio_dt_d + timedelta(days=dia)).strftime("%Y-%m-%d")
                    params_extra = _re.resolver_parametros_regla('PERSONAL_EXTRA_FUERA_MINIMO', emp.nombre, fecha_bloque, reglas_servicio_db, emp.reglas, {})
                    es_extra = False
                    if params_extra is not None and params_extra is not ... and isinstance(params_extra, dict):
                        nombres_extra_resueltos = params_extra.get('nombres', [])
                        if emp.nombre in nombres_extra_resueltos:
                            es_extra = True
                            
                    for d_off in [0, -1]:
                        dia_t = dia + d_off
                        if dia_t < 0:
                            if historial_semana_previa:
                                prev_guards = historial_semana_previa.get(emp.nombre, [])
                                fecha_ayer = (fecha_inicio_dt_d + timedelta(days=-1)).strftime("%Y-%m-%d")
                                for g in prev_guards:
                                    if g['fecha'] == fecha_ayer:
                                        t_prev_nombre = g['turno']
                                        if t_prev_nombre in turnos_dict:
                                            t_info = turnos_dict[t_prev_nombre]
                                            ts_abs = -1 * 24 + time_to_float(t_info.hora_inicio)
                                            te_abs = ts_abs + t_info.horas
                                            if ts_abs <= d_abs_start + 0.01 and te_abs >= d_abs_end - 0.01:
                                                if es_extra: pool_extras.append(1)
                                                else: pool_normales.append(1)
                            continue
                            
                        if dia_t in emp.dias_licencia: continue
                        
                        for t_nombre, t_info in turnos_dict.items():
                            if t_info.puesto_nombre != dem["puesto"]:
                                continue
                            if (emp.nombre, dia_t, t_nombre) in turnos_vars:
                                ts_abs = dia_t * 24 + time_to_float(t_info.hora_inicio)
                                te_abs = ts_abs + t_info.horas
                                if ts_abs <= d_abs_start + 0.01 and te_abs >= d_abs_end - 0.01:
                                    if es_extra: pool_extras.append(turnos_vars[(emp.nombre, dia_t, t_nombre)])
                                    else:
                                        pool_normales.append(turnos_vars[(emp.nombre, dia_t, t_nombre)])
                                        if dia_t >= 0:
                                            has_block_vars = True
                                            
                if c_min is not None and c_min > 0:
                    if d_abs_end <= 8 and not has_block_vars: pass
                    else: modelo.Add(sum(pool_normales) >= c_min)
                if c_max is not None:
                    modelo.Add(sum(pool_normales) + sum(pool_extras) <= c_max)

def test_model(day_to_skip=None, shift_to_skip=None):
    modelo = cp_model.CpModel()
    turnos = {}
    fecha_inicio_dt_d = date.fromisoformat(fecha_inicio)
    
    for emp in empleados:
        nombre = emp.nombre
        rol_persona = emp.rol
        licencia_dias = emp.dias_licencia
        for dia in range(total_dias):
            dia_semana = (dia + offset_dia) % 7
            es_finde_o_feriado = (dia_semana >= 5) or (dia in feriados_indices)
            tipo_dia = "Finde_Feriado" if es_finde_o_feriado else "Semana"
            lista_turnos = config_turnos.get(tipo_dia, {}).keys()
            
            for t in lista_turnos:
                t_info = turnos_dict.get(t)
                puesto_nombre_turno = t_info.puesto_nombre if t_info else None
                
                if puesto_nombre_turno:
                    if emp.puestos_habilitados:
                        if puesto_nombre_turno not in emp.puestos_habilitados:
                            continue
                    else:
                        if rol_persona and rol_persona != "Rotativo" and rol_persona != puesto_nombre_turno:
                            continue
                            
                turnos[(nombre, dia, t)] = modelo.NewBoolVar(f'turno_{nombre}_dia{dia}_{t}')
                
            vars_dia = [turnos[(nombre, dia, t)] for t in lista_turnos if (nombre, dia, t) in turnos]
            if vars_dia:
                modelo.Add(sum(vars_dia) <= 1)
                
    from hard_rules import (
        _crear_y_vincular_variables_semanales, _aplicar_licencias, _aplicar_franco_forzado,
        _aplicar_max_turnos, _aplicar_excluir_turnos, _aplicar_min_turnos,
        _aplicar_limite_horas_semanales, _aplicar_descanso_entre_turnos, _aplicar_min_findes_mes,
        _aplicar_findes_completos_y_medios, _aplicar_un_solo_turno_por_dia,
        _aplicar_max_horas_mes_calendario, _aplicar_fin_licencia, _aplicar_min_horas_mes_calendario,
        _aplicar_reglas_fechas_especiales, _aplicar_balance_dia_noche, _aplicar_personal_asociado,
        _aplicar_evitar_mezcla_semanal_dura, _aplicar_rotacion_mensual_dura
    )
    
    vars_turno_sem = _crear_y_vincular_variables_semanales(modelo, turnos, empleados, total_dias, fecha_inicio_dt_d, historial_semana_previa, offset_dia)
    
    _aplicar_licencias(modelo, turnos, empleados, config_turnos, offset_dia, feriados_indices)
    _aplicar_franco_forzado(modelo, turnos, empleados, total_dias, fecha_inicio_dt_d, config_turnos, reglas_servicio_db, ajustes_reglas)
    _aplicar_max_turnos(modelo, turnos, empleados, _get_semanas(total_dias, fecha_inicio_dt_d), reglas_servicio_db, ajustes_reglas, historial_semana_previa, total_dias, fecha_inicio_dt_d)
    _aplicar_excluir_turnos(modelo, turnos, empleados, total_dias, offset_dia, fecha_inicio_dt_d, reglas_servicio_db, ajustes_reglas)
    _aplicar_min_turnos(modelo, turnos, empleados, _get_semanas(total_dias, fecha_inicio_dt_d), reglas_servicio_db, ajustes_reglas, historial_semana_previa)
    
    custom_aplicar_cobertura_dinamica(modelo, turnos, day_to_skip, shift_to_skip)
    
    limite_horas_global = reglas_servicio_db.get('MAX_HORAS_SEMANA', {}).get('limite', 48)
    _aplicar_limite_horas_semanales(modelo, turnos, empleados, _get_semanas(total_dias, fecha_inicio_dt_d), reglas_servicio_db, ajustes_reglas, historial_semana_previa, config_turnos, turnos_dict, offset_dia, feriados_indices, limite_horas_global)
    _aplicar_descanso_entre_turnos(modelo, turnos, empleados, total_dias, fecha_inicio_dt_d, reglas_servicio_db, ajustes_reglas, offset_dia, feriados_indices, config_turnos, turnos_dict, historial_semana_previa)
    _aplicar_min_findes_mes(modelo, turnos, empleados, config_turnos, offset_dia, feriados_indices, reglas_servicio_db, ajustes_reglas, total_dias, servicio_id)
    _aplicar_findes_completos_y_medios(modelo, turnos, empleados, config_turnos, offset_dia, feriados_indices, reglas_servicio_db, ajustes_reglas, total_dias)
    _aplicar_un_solo_turno_por_dia(modelo, turnos, empleados, total_dias, offset_dia, feriados_indices, fecha_inicio_dt_d, config_turnos, reglas_servicio_db, ajustes_reglas)
    _aplicar_max_horas_mes_calendario(modelo, turnos, empleados, total_dias, offset_dia, feriados_indices, fecha_inicio_dt_d, config_turnos, turnos_dict, reglas_servicio_db, ajustes_reglas)
    _aplicar_fin_licencia(modelo, turnos, empleados, total_dias, offset_dia, feriados_indices, config_turnos, reglas_servicio_db, ajustes_reglas, fecha_inicio_dt_d)
    _aplicar_min_horas_mes_calendario(modelo, turnos, empleados, total_dias, offset_dia, feriados_indices, fecha_inicio_dt_d, config_turnos, turnos_dict, reglas_servicio_db, ajustes_reglas)
    _aplicar_reglas_fechas_especiales(modelo, turnos, empleados, total_dias, fecha_inicio_dt_d, config_turnos, reglas_servicio_db, ajustes_reglas)
    _aplicar_balance_dia_noche(modelo, turnos, empleados, total_dias, offset_dia, feriados_indices, config_turnos, turnos_dict, reglas_servicio_db, ajustes_reglas, fecha_inicio_dt_d)
    _aplicar_personal_asociado(modelo, turnos, empleados, total_dias, offset_dia, feriados_indices, config_turnos, turnos_dict, reglas_servicio_db, ajustes_reglas)
    
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 2.0
    status = solver.Solve(modelo)
    return status == cp_model.OPTIMAL or status == cp_model.FEASIBLE

def _get_semanas(dias, fecha_start):
    semanas = {}
    for d in range(dias):
        fecha_d = fecha_start + timedelta(days=d)
        iso_year, iso_week, iso_weekday = fecha_d.isocalendar()
        semanas.setdefault((iso_year, iso_week), []).append((d, fecha_d))
    return semanas

# Test day-by-day
print("--- Day-by-Day Cobertura testing ---")
feasible_days = []
for day in range(total_dias):
    if test_model(day_to_skip=day):
        fecha_d = date.fromisoformat(fecha_inicio) + timedelta(days=day)
        print(f"-> Model becomes FEASIBLE if Cobertura is disabled on Day {day} ({fecha_d.strftime('%Y-%m-%d')})")
        feasible_days.append(day)

# Test shift-by-shift
print("\n--- Shift-by-Shift Cobertura testing ---")
# Get unique start times of demands for service
shifts = sorted(list(set(dem["hora_inicio"] for k in demanda_req for dem in demanda_req[k])))
for shift in shifts:
    if test_model(shift_to_skip=shift):
        print(f"-> Model becomes FEASIBLE if Cobertura is disabled for Shift starting at {shift}")
