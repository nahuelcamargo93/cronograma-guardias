"""
Diagnóstico específico: ¿cuál regla de main.py causa infeasibilidad 
cuando EXACTO_DIA_ESPECIFICO_MES_HARD está activa?
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

# Usar main.py directamente para construir el modelo completo
from main import construir_modelo
from data import EVITAR_MEZCLA_SEMANAL_DURA, ROTACION_MENSUAL_DURA

def full_model_with_skip(skip_rule=None):
    """Construye el modelo completo de main.py y desactiva una regla opcional."""
    import copy
    
    # Hack: suspender la regla en reglas_servicio_copia
    reglas_copia = copy.deepcopy(reglas_servicio)
    if skip_rule and skip_rule in reglas_copia:
        del reglas_copia[skip_rule]
    
    modelo = cp_model.CpModel()
    turnos = {}
    fecha_inicio_d = date.fromisoformat(FECHA_INICIO)
    
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
    
    semanas_cal = _get_semanas_calendario(total_dias, fecha_inicio_d)
    limite_horas = reglas_copia.get('MAX_HORAS_SEMANA', {}).get('limite', 60)
    vars_turno_sem = _crear_y_vincular_variables_semanales(modelo, turnos, empleados, total_dias, fecha_inicio_d, historial, offset_dia)
    
    # Aplicar todas las reglas del modelo completo (igual que aplicar_reglas_duras)
    _aplicar_licencias(modelo, turnos, empleados, config_turnos, offset_dia, feriados_indices)
    _aplicar_franco_forzado(modelo, turnos, empleados, total_dias, fecha_inicio_d, config_turnos, reglas_copia, ajustes_reglas)
    _aplicar_max_turnos(modelo, turnos, empleados, semanas_cal, reglas_copia, ajustes_reglas, historial, total_dias, fecha_inicio_d)
    _aplicar_excluir_turnos(modelo, turnos, empleados, total_dias, offset_dia, fecha_inicio_d, reglas_copia, ajustes_reglas)
    _aplicar_min_turnos(modelo, turnos, empleados, semanas_cal, reglas_copia, ajustes_reglas, historial)
    _aplicar_cobertura_dinamica(modelo, turnos, empleados, demanda_req, ajustes_db, total_dias, feriados_indices, offset_dia, turnos_dict, fecha_inicio_d, historial, reglas_copia, ajustes_reglas)
    _aplicar_limite_horas_semanales(modelo, turnos, empleados, semanas_cal, reglas_copia, ajustes_reglas, historial, config_turnos, turnos_dict, offset_dia, feriados_indices, limite_horas)
    _aplicar_descanso_entre_turnos(modelo, turnos, empleados, total_dias, fecha_inicio_d, reglas_copia, ajustes_reglas, offset_dia, feriados_indices, config_turnos, turnos_dict, historial)
    _aplicar_min_findes_mes(modelo, turnos, empleados, config_turnos, offset_dia, feriados_indices, reglas_copia, ajustes_reglas, total_dias, SERVICIO_ID)
    _aplicar_exacto_dia_especifico_mes_hard(modelo, turnos, empleados, config_turnos, offset_dia, feriados_indices, reglas_copia, ajustes_reglas, total_dias, turnos_dict)
    _aplicar_findes_completos_y_medios(modelo, turnos, empleados, config_turnos, offset_dia, feriados_indices, reglas_copia, ajustes_reglas, total_dias)
    _aplicar_un_solo_turno_por_dia(modelo, turnos, empleados, total_dias, offset_dia, feriados_indices, fecha_inicio_d, config_turnos, reglas_copia, ajustes_reglas)
    _aplicar_patron_ciclico(modelo, turnos, empleados, total_dias, fecha_inicio_d, config_turnos, reglas_copia, ajustes_reglas, historial)
    _aplicar_max_horas_mes_calendario(modelo, turnos, empleados, total_dias, offset_dia, feriados_indices, fecha_inicio_d, config_turnos, turnos_dict, reglas_copia, ajustes_reglas)
    _aplicar_fin_licencia(modelo, turnos, empleados, total_dias, offset_dia, feriados_indices, config_turnos, reglas_copia, ajustes_reglas, fecha_inicio_d)
    _aplicar_min_horas_mes_calendario(modelo, turnos, empleados, total_dias, offset_dia, feriados_indices, fecha_inicio_d, config_turnos, turnos_dict, reglas_copia, ajustes_reglas)
    _aplicar_reglas_fechas_especiales(modelo, turnos, empleados, total_dias, fecha_inicio_d, config_turnos, reglas_copia, ajustes_reglas)
    _aplicar_balance_dia_noche(modelo, turnos, empleados, total_dias, offset_dia, feriados_indices, config_turnos, turnos_dict, reglas_copia, ajustes_reglas, fecha_inicio_d)
    _aplicar_personal_asociado(modelo, turnos, empleados, total_dias, offset_dia, feriados_indices, config_turnos, turnos_dict, reglas_copia, ajustes_reglas)
    _aplicar_max_dias_continuos(modelo, turnos, empleados, total_dias, fecha_inicio_d, offset_dia, feriados_indices, config_turnos, turnos_dict, reglas_copia, ajustes_reglas, historial)
    
    return modelo

def intentar(modelo, label, timeout=8):
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = timeout
    status = solver.Solve(modelo)
    ok = status in [cp_model.OPTIMAL, cp_model.FEASIBLE]
    print(f"  [{'OK' if ok else 'FAIL'}] {label}")
    return ok

print("=== Diagnóstico: ¿qué regla causa el conflicto con EXACTO_DIA_ESPECIFICO_MES_HARD? ===\n")

m_base = full_model_with_skip(None)
if intentar(m_base, "Modelo completo (todas las reglas)"):
    print("FACTIBLE - no hay problema")
else:
    reglas_a_probar = [
        'ASIGNACION_FIJA', 'PATRON_CICLICO', 'REGLAS_FECHAS_ESPECIALES',
        'BALANCE_DIA_NOCHE', 'PERSONAL_ASOCIADO', 'MAX_DIAS_CONTINUOS',
        'FINS_COMPLETOS_Y_MEDIOS', 'UN_SOLO_TURNO_POR_DIA',
        'MIN_HORAS_MES_CALENDARIO', 'MAX_HORAS_MES_CALENDARIO', 'FIN_LICENCIA',
        'MAX_TURNOS', 'MIN_TURNOS', 'LIMITE_HORAS_SEMANALES',
    ]
    print("Intentando desactivar cada regla:")
    for r in reglas_a_probar:
        m = full_model_with_skip(r)
        if intentar(m, f"Sin {r}"):
            print(f"  *** {r} ES EL CULPABLE ***")
