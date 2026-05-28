"""
Test: ¿es la infeasibilidad con ASIGNACION_FIJA o sin ella?
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

db_queries.init_licencias()
fecha_ini_dt = datetime.datetime.strptime(FECHA_INICIO, '%Y-%m-%d')
total_dias = (datetime.datetime.strptime(FECHA_FIN, '%Y-%m-%d') - fecha_ini_dt).days + 1
offset_dia = fecha_ini_dt.weekday()
feriados_idx = [(datetime.datetime.strptime(f, '%Y-%m-%d') - fecha_ini_dt).days 
                for f in FERIADOS if 0 <= (datetime.datetime.strptime(f, '%Y-%m-%d') - fecha_ini_dt).days < total_dias]
config, _, dreq, adj = db_queries.cargar_configuracion_turnos(servicio_id=SERVICIO_ID, fecha_inicio=FECHA_INICIO, fecha_fin=FECHA_FIN)
rs = db_queries.cargar_reglas_servicio(SERVICIO_ID)
aj = db_queries.cargar_ajustes_reglas_personal(FECHA_INICIO, FECHA_FIN)
emps = obtener_empleados(SERVICIO_ID, FECHA_INICIO, total_dias)
td = obtener_turnos(SERVICIO_ID)
hist = db_queries.cargar_guardias_previas(FECHA_INICIO, dias_atras=28, servicio_id=SERVICIO_ID)
mapa = {'Lunes': 0, 'Martes': 1, 'Miercoles': 2, 'Jueves': 3, 'Viernes': 4, 'Sabado': 5, 'Domingo': 6}

def run_test(label, with_asig_fija):
    m = cp_model.CpModel()
    t = {}
    fd = date.fromisoformat(FECHA_INICIO)
    for emp in emps:
        for dia in range(total_dias):
            ds = (dia + offset_dia) % 7
            tipo = 'Finde_Feriado' if (ds >= 5 or dia in feriados_idx) else 'Semana'
            lt = list(config.get(tipo, {}).keys())
            for tk in lt:
                ti = td.get(tk)
                pn = ti.puesto_nombre if ti else None
                if pn and emp.puestos_habilitados and pn not in emp.puestos_habilitados:
                    continue
                t[(emp.nombre, dia, tk)] = m.NewBoolVar(f'x_{emp.nombre}_{dia}_{tk}')
            
            if with_asig_fija and dia not in emp.dias_licencia:
                fds = (fd + timedelta(days=dia)).isoformat()
                p = _re.resolver_parametros_regla('ASIGNACION_FIJA', emp.nombre, fds, rs, emp.reglas, aj or {})
                if _re.regla_existe(p) and isinstance(p, list):
                    for asig in p:
                        fa = asig.get('Fecha')
                        da = asig.get('Dia')
                        match = (fa and fa == fds) or (da and mapa.get(da) == ds)
                        if match:
                            tc = asig['Turno'].replace(' ', '_')
                            vc = [t[(emp.nombre, dia, tk)] for tk in lt 
                                  if (emp.nombre, dia, tk) in t and (tk == tc or tk.startswith(tc + '_'))]
                            if vc:
                                m.Add(sum(vc) == 1)
            
            tipo_var = 'Finde_Feriado' if (ds >= 5 or dia in feriados_idx) else 'Semana'
            vd = [t[(emp.nombre, dia, tk)] for tk in config.get(tipo_var, {}).keys() if (emp.nombre, dia, tk) in t]
            if vd:
                m.Add(sum(vd) <= 1)
    
    aplicar_reglas_duras(m, t, emps, config, td, dreq, adj, total_dias, feriados_idx, offset_dia, (total_dias+6)//7, hist, rs, aj, SERVICIO_ID)
    
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 15
    status = solver.Solve(m)
    ok = status in [cp_model.OPTIMAL, cp_model.FEASIBLE]
    print(f"[{'OK' if ok else 'FAIL'}] {label}")
    return ok

print("=== Test ASIGNACION_FIJA + EXACTO_DIA_HARD ===")
run_test('Con ASIGNACION_FIJA', True)
run_test('Sin ASIGNACION_FIJA', False)
