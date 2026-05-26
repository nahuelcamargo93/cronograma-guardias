import sys
import os
from datetime import date, timedelta
from ortools.sat.python import cp_model

sys.path.append(os.getcwd())

import data
from database import queries as db_queries
from database.data_loader import obtener_empleados, obtener_turnos
import rule_engine as _re
from debug_imposibilidad import construir_modelo_test, intentar_resolver

# We will write a custom solver that adds slack to MIN_HORAS_MES_CALENDARIO
db_queries.init_licencias()
fecha_inicio = data.FECHA_INICIO
fecha_fin = data.FECHA_FIN
servicio_id = 2

config_turnos, _, demanda_req, ajustes_db = db_queries.cargar_configuracion_turnos(
    servicio_id=servicio_id, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin
)
turnos_dict = obtener_turnos(servicio_id)
reglas_servicio_db = db_queries.cargar_reglas_servicio(servicio_id)
ajustes_reglas = db_queries.cargar_ajustes_reglas_personal(fecha_inicio, fecha_fin)
empleados = obtener_empleados(servicio_id, fecha_inicio, 31)
historial_semana_previa = db_queries.cargar_guardias_previas(fecha_inicio, dias_atras=28, servicio_id=servicio_id)
offset_dia = 2 # July 1st 2026 is Wednesday
dias_del_bloque = 31
feriados = [9] # July 9th
num_semanas = 5

# Let's reconstruct the model with slacks on MIN_HORAS_MES_CALENDARIO
modelo = cp_model.CpModel()
turnos = {}
mapa_dias = {"Lunes": 0, "Martes": 1, "Miercoles": 2, "Jueves": 3, "Viernes": 4, "Sabado": 5, "Domingo": 6}

# Create variables
for emp in empleados:
    nombre = emp.nombre
    rol_persona = emp.rol
    licencia_dias = emp.dias_licencia
    for dia in range(dias_del_bloque):
        dia_semana = (dia + offset_dia) % 7
        es_finde_o_feriado = (dia_semana >= 5) or (dia in feriados)
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

# Import hard rules
from hard_rules import (
    _aplicar_licencias, _aplicar_franco_forzado, _aplicar_max_turnos,
    _aplicar_excluir_turnos, _aplicar_min_turnos, _aplicar_cobertura_dinamica,
    _aplicar_limite_horas_semanales, _aplicar_descanso_entre_turnos,
    _aplicar_min_findes_mes, _aplicar_un_solo_turno_por_dia,
    _aplicar_max_horas_mes_calendario, _aplicar_fin_licencia,
    _aplicar_reglas_fechas_especiales, _aplicar_patron_ciclico,
    _get_semanas_calendario, _crear_y_vincular_variables_semanales,
    _aplicar_evitar_mezcla_semanal_dura, _aplicar_rotacion_mensual_dura
)

# Apply all rules except MIN_HORAS_MES_CALENDARIO, which we will apply with slack
_aplicar_licencias(modelo, turnos, empleados, config_turnos, offset_dia, feriados)
_aplicar_franco_forzado(modelo, turnos, empleados, dias_del_bloque, date.fromisoformat(fecha_inicio), config_turnos, reglas_servicio_db, ajustes_reglas)
_aplicar_max_turnos(modelo, turnos, empleados, _get_semanas_calendario(dias_del_bloque, date.fromisoformat(fecha_inicio)), reglas_servicio_db, ajustes_reglas, historial_semana_previa, dias_del_bloque, date.fromisoformat(fecha_inicio))
_aplicar_excluir_turnos(modelo, turnos, empleados, dias_del_bloque, offset_dia, date.fromisoformat(fecha_inicio), reglas_servicio_db, ajustes_reglas)
_aplicar_min_turnos(modelo, turnos, empleados, _get_semanas_calendario(dias_del_bloque, date.fromisoformat(fecha_inicio)), reglas_servicio_db, ajustes_reglas, historial_semana_previa)
_aplicar_cobertura_dinamica(modelo, turnos, empleados, demanda_req, ajustes_db, dias_del_bloque, feriados, offset_dia, turnos_dict, date.fromisoformat(fecha_inicio), historial_semana_previa, reglas_servicio_db, ajustes_reglas)
_aplicar_limite_horas_semanales(modelo, turnos, empleados, _get_semanas_calendario(dias_del_bloque, date.fromisoformat(fecha_inicio)), reglas_servicio_db, ajustes_reglas, historial_semana_previa, config_turnos, turnos_dict, offset_dia, feriados, 48)
_aplicar_descanso_entre_turnos(modelo, turnos, empleados, dias_del_bloque, date.fromisoformat(fecha_inicio), reglas_servicio_db, ajustes_reglas, offset_dia, feriados, config_turnos, turnos_dict, historial_semana_previa)
_aplicar_min_findes_mes(modelo, turnos, empleados, config_turnos, offset_dia, feriados, reglas_servicio_db, ajustes_reglas, dias_del_bloque, servicio_id)
_aplicar_un_solo_turno_por_dia(modelo, turnos, empleados, dias_del_bloque, offset_dia, feriados, date.fromisoformat(fecha_inicio), config_turnos, reglas_servicio_db, ajustes_reglas)
_aplicar_max_horas_mes_calendario(modelo, turnos, empleados, dias_del_bloque, offset_dia, feriados, date.fromisoformat(fecha_inicio), config_turnos, turnos_dict, reglas_servicio_db, ajustes_reglas)
_aplicar_fin_licencia(modelo, turnos, empleados, dias_del_bloque, offset_dia, feriados, config_turnos, reglas_servicio_db, ajustes_reglas, date.fromisoformat(fecha_inicio))
_aplicar_reglas_fechas_especiales(modelo, turnos, empleados, dias_del_bloque, date.fromisoformat(fecha_inicio), config_turnos, reglas_servicio_db, ajustes_reglas)
_aplicar_patron_ciclico(modelo, turnos, empleados, dias_del_bloque, date.fromisoformat(fecha_inicio), config_turnos, reglas_servicio_db, ajustes_reglas, historial_semana_previa)

vars_turno_sem = _crear_y_vincular_variables_semanales(modelo, turnos, empleados, dias_del_bloque, date.fromisoformat(fecha_inicio), historial_semana_previa, offset_dia)
_aplicar_evitar_mezcla_semanal_dura(modelo, vars_turno_sem, empleados, dias_del_bloque, date.fromisoformat(fecha_inicio))
_aplicar_rotacion_mensual_dura(modelo, vars_turno_sem, empleados, dias_del_bloque, date.fromisoformat(fecha_inicio), reglas_servicio_db, ajustes_reglas)

# MIN_HORAS_MES_CALENDARIO with slack
slacks = {}
fecha_inicio_dt = date.fromisoformat(fecha_inicio)

for emp in empleados:
    meses = {}
    for d in range(dias_del_bloque):
        m_key = (fecha_inicio_dt + timedelta(days=d)).strftime("%Y-%m")
        meses.setdefault(m_key, []).append(d)
        
    for m_key, dias_m in meses.items():
        ref_date = (fecha_inicio_dt + timedelta(days=dias_m[0])).isoformat()
        p_min = _re.resolver_parametros_regla('MIN_HORAS_MES_CALENDARIO', emp.nombre, ref_date, reglas_servicio_db, emp.reglas, ajustes_reglas)
        p_max = _re.resolver_parametros_regla('MAX_HORAS_MES_CALENDARIO', emp.nombre, ref_date, reglas_servicio_db, emp.reglas, ajustes_reglas)
        
        if _re.regla_existe(p_min) and not _re.regla_suspendida(p_min):
            min_h = p_min.get('min_horas', 144) if isinstance(p_min, dict) else 144
            
            if not _re.regla_suspendida(p_max):
                max_h_ref = p_max.get('max_horas', 192) if isinstance(p_max, dict) else 192
                if min_h > max_h_ref:
                    min_h = max_h_ref
            
            vars_h = []
            for d in dias_m:
                td = "Finde_Feriado" if ((d + offset_dia) % 7 >= 5 or d in feriados) else "Semana"
                for t in config_turnos.get(td, {}).keys():
                    if (emp.nombre, d, t) in turnos:
                        h_turno = turnos_dict[t].horas
                        vars_h.append(turnos[(emp.nombre, d, t)] * h_turno)
            
            dias_lic = [d for d in dias_m if d in emp.dias_licencia]
            p_cred = _re.resolver_parametros_regla('CREDITO_HORARIO_LICENCIA', emp.nombre, ref_date, reglas_servicio_db, emp.reglas, ajustes_reglas)
            if _re.regla_existe(p_cred):
                h_sem = p_cred.get('horas_por_semana', 36)
                horas_lic = int((h_sem / 7.0) * len(dias_lic) + 0.5)
            else:
                horas_lic = int((float(min_h) / dias_del_bloque) * len(dias_lic) + 0.5)

            piso = int((min_h / dias_del_bloque) * len(dias_m) + 0.5)
            
            if vars_h:
                # Add a slack variable (in hours, integer >= 0)
                slack = modelo.NewIntVar(0, 200, f'slack_{emp.nombre}_{m_key}')
                modelo.Add(sum(vars_h) + horas_lic + slack >= piso)
                slacks[(emp.nombre, m_key)] = {
                    'slack': slack,
                    'piso': piso,
                    'horas_lic': horas_lic,
                    'min_h': min_h,
                    'lic_days': len(dias_lic),
                    'vars_h': vars_h
                }

# Minimize total slack
modelo.Minimize(sum(info['slack'] for info in slacks.values()))

solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 20
status = solver.Solve(modelo)

if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
    print(f"Model solved! Objective (total slack hours): {solver.ObjectiveValue()}")
    print("\nIndividual slack analysis:")
    for (nombre, m_key), info in slacks.items():
        slack_val = solver.Value(info['slack'])
        if slack_val > 0 or info['lic_days'] > 0:
            actual_worked = sum(solver.Value(v) for v in info['vars_h'])
            print(f"Emp: {nombre:25s} | Licencias: {info['lic_days']} | Piso: {info['piso']} | Credito Lic: {info['horas_lic']} | Real Trabajado: {actual_worked} | Slack: {slack_val}")
else:
    print("Even with slacks, model is infeasible! (This means other rules are also impossible together)")
