"""
Test definitivo: ¿el conflicto viene de la coexistencia de 
EXACTO_DIA_ESPECIFICO_MES_HARD (hard) + EXACTO_DIA_ESPECIFICO_MES (soft)?
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
from hard_rules import aplicar_reglas_duras
from soft_rules import aplicar_reglas_blandas

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
mapa_dias = {"Lunes": 0, "Martes": 1, "Miercoles": 2, "Jueves": 3, "Viernes": 4, "Sabado": 5, "Domingo": 6}

def build_variables(modelo, include_asignacion_fija=True):
    turnos = {}
    fecha_inicio_d = date.fromisoformat(FECHA_INICIO)
    for emp in empleados:
        nombre = emp.nombre
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
                turnos[(nombre, dia, t)] = modelo.NewBoolVar(f'turno_{nombre}_dia{dia}_{t}')
            
            if include_asignacion_fija and dia not in emp.dias_licencia:
                fecha_dia_str = (fecha_inicio_d + timedelta(days=dia)).isoformat()
                params = _re.resolver_parametros_regla('ASIGNACION_FIJA', nombre, fecha_dia_str, reglas_servicio, emp.reglas, ajustes_reglas or {})
                if _re.regla_existe(params) and isinstance(params, list):
                    for asig in params:
                        fecha_asig = asig.get('Fecha')
                        dia_asig = asig.get('Dia')
                        match = (fecha_asig and fecha_asig == fecha_dia_str) or (dia_asig and mapa_dias.get(dia_asig) == dia_semana)
                        if match:
                            turno_config = asig['Turno'].replace(" ", "_")
                            vars_coinc = [turnos[(nombre, dia, t)] for t in lista_turnos if (nombre, dia, t) in turnos and (t == turno_config or t.startswith(turno_config + "_"))]
                            if vars_coinc:
                                modelo.Add(sum(vars_coinc) == 1)
            
            vars_dia = [turnos[(nombre, dia, t)] for t in config_turnos.get("Finde_Feriado" if (dia_semana >= 5 or dia in feriados_indices) else "Semana", {}).keys() if (nombre, dia, t) in turnos]
            if vars_dia:
                modelo.Add(sum(vars_dia) <= 1)
    return turnos

def intentar(modelo, label):
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 15
    status = solver.Solve(modelo)
    ok = status in [cp_model.OPTIMAL, cp_model.FEASIBLE]
    print(f"  [{'OK' if ok else 'FAIL'}] {label}")
    return ok

print("=== Test: Hard + Soft combinados ===\n")

# Test 1: Hard + Soft (como en main.py)
m1 = cp_model.CpModel()
t1 = build_variables(m1)
aplicar_reglas_duras(m1, t1, empleados, config_turnos, turnos_dict, demanda_req, ajustes_db, total_dias, feriados_indices, offset_dia, num_semanas, historial, reglas_servicio, ajustes_reglas, SERVICIO_ID)
aplicar_reglas_blandas(m1, t1, empleados, config_turnos, turnos_dict, total_dias, feriados_indices, offset_dia, num_semanas, SERVICIO_ID, {}, historial, demanda_req=demanda_req, ajustes_demanda=ajustes_db)
intentar(m1, "Hard + Soft (igual que main.py)")
