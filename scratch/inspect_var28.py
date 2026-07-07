import sys
import os
from datetime import date, timedelta
from ortools.sat.python import cp_model

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import main
from database import queries as db_queries
from database import schema as db_schema
from database.data_loader import obtener_empleados, obtener_turnos

def main_inspect():
    db_schema.inicializar_db()
    db_queries.init_licencias(3)
    
    fecha_inicio = "2026-07-01"
    fecha_fin = "2026-07-31"
    fecha_inicio_dt = date.fromisoformat(fecha_inicio)
    fecha_fin_dt = date.fromisoformat(fecha_fin)
    dias_del_bloque = (fecha_fin_dt - fecha_inicio_dt).days + 1
    offset_dia = fecha_inicio_dt.weekday()
    
    lunes_unicos = set()
    for d in range(dias_del_bloque):
        fecha_d = fecha_inicio_dt + timedelta(days=d)
        lunes = fecha_d - timedelta(days=fecha_d.weekday())
        lunes_unicos.add(lunes)
    num_semanas = len(lunes_unicos)

    feriados_indices = []
    feriados_db = db_queries.obtener_feriados(fecha_inicio, fecha_fin, servicio_id=3)
    for f_str in feriados_db:
        f_dt = date.fromisoformat(f_str)
        delta = (f_dt - fecha_inicio_dt).days
        if 0 <= delta < dias_del_bloque:
            feriados_indices.append(delta)

    config_turnos, turnos_info, demanda_req, ajustes_db = db_queries.cargar_configuracion_turnos(
        servicio_id=3, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin
    )
    reglas_servicio_db = db_queries.cargar_reglas_servicio(3)
    ajustes_reglas = db_queries.cargar_ajustes_reglas_personal(fecha_inicio, fecha_fin)
    ajustes_servicio = db_queries.cargar_ajustes_reglas_servicio(fecha_inicio, fecha_fin, 3)
    ajustes_reglas['__servicio__'] = ajustes_servicio
    
    empleados = obtener_empleados(3, fecha_inicio, dias_del_bloque)
    turnos_dict = obtener_turnos(3)
    historial_semana_previa = db_queries.cargar_guardias_previas(fecha_inicio, dias_atras=28, servicio_id=3)

    modelo, turnos, flr_tracker, ctx = main.construir_modelo(
        empleados, config_turnos, turnos_dict, demanda_req, ajustes_db,
        dias_del_bloque, feriados_indices, offset_dia, num_semanas,
        reglas_servicio=reglas_servicio_db,
        ajustes_reglas_personal=ajustes_reglas,
        historial_semana_previa=historial_semana_previa,
        servicio_id=3,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        modo_debug=False,
        force_assumptions=True,
        cronograma_base_guardias=None,
        lock_fecha_inicio=None,
        lock_fecha_fin=None
    )
    
    proto = modelo.Proto()
    print("Variable 28 details:")
    v = proto.variables[28]
    print(f"Name: {v.name}")
    print(f"Domain: {v.domain}")
    
    print("\nConstraints containing variable 28:")
    for idx, c in enumerate(proto.constraints):
        lin = c.linear
        if 28 in lin.vars:
            print(f"Constraint {idx}: name='{c.name}'")
            vars_str = []
            for v_idx in lin.vars:
                vars_str.append(f"var_{v_idx} ({proto.variables[v_idx].name})")
            print(f"  linear vars: {', '.join(vars_str)}")
            print(f"  coeffs: {list(lin.coeffs)}")
            print(f"  domain: {list(lin.domain)}")

if __name__ == '__main__':
    main_inspect()
