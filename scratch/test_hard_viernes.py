"""
Test rápido: con EXACTO_DIA_ESPECIFICO_MES_HARD desactivada, ¿es factible?
Y con ella activa pero DESCANSO_ENTRE_TURNOS o COBERTURA_DINAMICA relajados, ¿funciona?
"""
import sys, os
sys.path.append(os.path.abspath('.'))
import datetime
from datetime import date, timedelta
from ortools.sat.python import cp_model

from data import FECHA_INICIO, FECHA_FIN, FERIADOS, SERVICIO_ID
from database import queries as db_queries
from database.data_loader import obtener_empleados, obtener_turnos
import rule_engine as _re

from hard_rules import (
    _aplicar_licencias, _aplicar_franco_forzado, _aplicar_max_turnos,
    _aplicar_excluir_turnos, _aplicar_min_turnos, _aplicar_cobertura_dinamica,
    _aplicar_limite_horas_semanales, _aplicar_descanso_entre_turnos,
    _aplicar_min_findes_mes, _aplicar_un_solo_turno_por_dia,
    _aplicar_max_horas_mes_calendario, _aplicar_fin_licencia,
    _aplicar_min_horas_mes_calendario, _aplicar_reglas_fechas_especiales,
    _aplicar_patron_ciclico, _get_semanas_calendario,
    _crear_y_vincular_variables_semanales, _aplicar_evitar_mezcla_semanal_dura,
    _aplicar_rotacion_mensual_dura, _aplicar_findes_completos_y_medios,
    _aplicar_balance_dia_noche, _aplicar_personal_asociado, _aplicar_max_dias_continuos,
    _aplicar_exacto_dia_especifico_mes_hard
)

db_queries.init_licencias()

fecha_inicio_dt = datetime.datetime.strptime(FECHA_INICIO, "%Y-%m-%d")
fecha_fin_dt    = datetime.datetime.strptime(FECHA_FIN,    "%Y-%m-%d")
total_dias = (fecha_fin_dt - fecha_inicio_dt).days + 1
num_semanas = (total_dias + 6) // 7
offset_dia = fecha_inicio_dt.weekday()
feriados_indices = [
    (datetime.datetime.strptime(f, "%Y-%m-%d") - fecha_inicio_dt).days
    for f in FERIADOS
    if 0 <= (datetime.datetime.strptime(f, "%Y-%m-%d") - fecha_inicio_dt).days < total_dias
]

config_turnos, _, demanda_req, ajustes_db = db_queries.cargar_configuracion_turnos(
    servicio_id=SERVICIO_ID, fecha_inicio=FECHA_INICIO, fecha_fin=FECHA_FIN
)
reglas_servicio = db_queries.cargar_reglas_servicio(SERVICIO_ID)
ajustes_reglas = db_queries.cargar_ajustes_reglas_personal(FECHA_INICIO, FECHA_FIN)
empleados = obtener_empleados(SERVICIO_ID, FECHA_INICIO, total_dias)
turnos_dict = obtener_turnos(SERVICIO_ID)
historial = db_queries.cargar_guardias_previas(FECHA_INICIO, dias_atras=28, servicio_id=SERVICIO_ID)

def build_and_solve(skip_hard_viernes=False, label=""):
    modelo = cp_model.CpModel()
    turnos = {}
    fecha_d = date.fromisoformat(FECHA_INICIO)

    for emp in empleados:
        for dia in range(total_dias):
            dia_semana = (dia + offset_dia) % 7
            es_finde = (dia_semana >= 5) or (dia in feriados_indices)
            tipo_dia = "Finde_Feriado" if es_finde else "Semana"
            lista_turnos = config_turnos.get(tipo_dia, {}).keys()
            for t in lista_turnos:
                t_info = turnos_dict.get(t)
                puesto_nombre = t_info.puesto_nombre if t_info else None
                if puesto_nombre and emp.puestos_habilitados and puesto_nombre not in emp.puestos_habilitados:
                    continue
                turnos[(emp.nombre, dia, t)] = modelo.NewBoolVar(f'turno_{emp.nombre}_{dia}_{t}')
            vars_dia = [turnos[(emp.nombre, dia, t)] for t in lista_turnos if (emp.nombre, dia, t) in turnos]
            if vars_dia:
                modelo.Add(sum(vars_dia) <= 1)

    fecha_inicio_d = date.fromisoformat(FECHA_INICIO)
    semanas_cal = _get_semanas_calendario(total_dias, fecha_inicio_d)
    limite_horas = reglas_servicio.get('MAX_HORAS_SEMANA', {}).get('limite', 60)
    vars_turno_sem = _crear_y_vincular_variables_semanales(modelo, turnos, empleados, total_dias, fecha_inicio_d, historial, offset_dia)

    _aplicar_licencias(modelo, turnos, empleados, config_turnos, offset_dia, feriados_indices)
    _aplicar_franco_forzado(modelo, turnos, empleados, total_dias, fecha_inicio_d, config_turnos, reglas_servicio, ajustes_reglas)
    _aplicar_max_turnos(modelo, turnos, empleados, semanas_cal, reglas_servicio, ajustes_reglas, historial, total_dias, fecha_inicio_d)
    _aplicar_excluir_turnos(modelo, turnos, empleados, total_dias, offset_dia, fecha_inicio_d, reglas_servicio, ajustes_reglas)
    _aplicar_min_turnos(modelo, turnos, empleados, semanas_cal, reglas_servicio, ajustes_reglas, historial)
    _aplicar_cobertura_dinamica(modelo, turnos, empleados, demanda_req, ajustes_db, total_dias, feriados_indices, offset_dia, turnos_dict, fecha_inicio_d, historial, reglas_servicio, ajustes_reglas)
    _aplicar_limite_horas_semanales(modelo, turnos, empleados, semanas_cal, reglas_servicio, ajustes_reglas, historial, config_turnos, turnos_dict, offset_dia, feriados_indices, limite_horas)
    _aplicar_descanso_entre_turnos(modelo, turnos, empleados, total_dias, fecha_inicio_d, reglas_servicio, ajustes_reglas, offset_dia, feriados_indices, config_turnos, turnos_dict, historial)
    _aplicar_min_findes_mes(modelo, turnos, empleados, config_turnos, offset_dia, feriados_indices, reglas_servicio, ajustes_reglas, total_dias, SERVICIO_ID)
    _aplicar_findes_completos_y_medios(modelo, turnos, empleados, config_turnos, offset_dia, feriados_indices, reglas_servicio, ajustes_reglas, total_dias)
    _aplicar_max_horas_mes_calendario(modelo, turnos, empleados, total_dias, offset_dia, feriados_indices, fecha_inicio_d, config_turnos, turnos_dict, reglas_servicio, ajustes_reglas)
    _aplicar_min_horas_mes_calendario(modelo, turnos, empleados, total_dias, offset_dia, feriados_indices, fecha_inicio_d, config_turnos, turnos_dict, reglas_servicio, ajustes_reglas)
    _aplicar_max_dias_continuos(modelo, turnos, empleados, total_dias, fecha_inicio_d, offset_dia, feriados_indices, config_turnos, turnos_dict, reglas_servicio, ajustes_reglas, historial)

    if not skip_hard_viernes:
        _aplicar_exacto_dia_especifico_mes_hard(modelo, turnos, empleados, config_turnos, offset_dia, feriados_indices, reglas_servicio, ajustes_reglas, total_dias, turnos_dict)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 15
    status = solver.Solve(modelo)
    factible = status in [cp_model.OPTIMAL, cp_model.FEASIBLE]
    print(f"[{'OK' if factible else 'FAIL'}] {label}: {'FACTIBLE' if factible else 'INVIABLE'}")
    return factible

print("=== Test EXACTO_DIA_ESPECIFICO_MES_HARD ===\n")
build_and_solve(skip_hard_viernes=True,  label="Sin regla hard viernes (baseline)")
build_and_solve(skip_hard_viernes=False, label="Con regla hard viernes")
