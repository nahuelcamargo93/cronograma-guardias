import sys
import os
import shutil
from ortools.sat.python import cp_model

sys.path.append(os.getcwd())

import data
import main
from database import queries as db_queries
from database.data_loader import obtener_empleados, obtener_turnos

def run_test(rule_to_disable):
    shutil.copy("soft_rules.py", "scratch/soft_rules_temp.py")
    
    with open("scratch/soft_rules_temp.py", "r", encoding="utf-8") as f:
        content = f.read()
        
    # Silence debug prints
    content = content.replace(
        'print(f"DEBUG: Penalizando {nombre} dia {d} turno {t_a_penalizar} peso {peso} es_f={es_f}")',
        'pass # print(...)'
    )
    
    # We can patch resolver_parametros_regla in the resolver call by returning None/Ellipsis or suspending it
    # But a cleaner way is to mock rule_engine.resolver_parametros_regla inside soft_rules_temp
    # Or simply replace resolver_parametros_regla(codigo, ...) with ... based on the code
    if rule_to_disable:
        content = content.replace(
            f"resolver_parametros_regla('{rule_to_disable}'",
            f"resolver_parametros_regla('DISABLED_RULE_{rule_to_disable}'"
        )
        # Also handle MIN_DIA_ESPECIFICO_MES and EXACTO_DIA_ESPECIFICO_MES together
        if rule_to_disable == "MIN_DIA_ESPECIFICO_MES":
            content = content.replace(
                "resolver_parametros_regla('EXACTO_DIA_ESPECIFICO_MES'",
                "resolver_parametros_regla('DISABLED_RULE_EXACTO_DIA_ESPECIFICO_MES'"
            )
            content = content.replace(
                "_aplicar_min_dia_especifico_mes_soft(modelo, turnos, empleados, turnos_dict, reglas_servicio, ajustes_personal, dias_del_bloque, fecha_inicio_dt, penalizaciones_ad_hoc, servicio_id)",
                "pass"
            )
            
        # Handle FLR rules
        if rule_to_disable == "FINDE_LARGO_REGLAMENTARIO":
            content = content.replace(
                "resolver_parametros_regla('FINDE_LARGO_REGLAMENTARIO_ESTRICTO'",
                "resolver_parametros_regla('DISABLED_RULE_FINDE_LARGO_REGLAMENTARIO_ESTRICTO'"
            )
            content = content.replace(
                "if active_flr_rule:",
                "if False:"
            )

    with open("scratch/soft_rules_temp.py", "w", encoding="utf-8") as f:
        f.write(content)
        
    if "scratch.soft_rules_temp" in sys.modules:
        del sys.modules["scratch.soft_rules_temp"]
    import scratch.soft_rules_temp as soft_rules_temp
    
    main.aplicar_reglas_blandas = soft_rules_temp.aplicar_reglas_blandas
    
    db_queries.init_licencias()
    config_turnos, metadata_turnos_raw, demanda_req, adjustments = db_queries.cargar_configuracion_turnos(
        servicio_id=data.SERVICIO_ID, fecha_inicio=data.FECHA_INICIO, fecha_fin=data.FECHA_FIN
    )
    reglas_servicio_db = db_queries.cargar_reglas_servicio(data.SERVICIO_ID)
    ajustes_reglas = db_queries.cargar_ajustes_reglas_personal(data.FECHA_INICIO, data.FECHA_FIN)
    empleados = obtener_empleados(data.SERVICIO_ID, data.FECHA_INICIO, 31)
    turnos_dict = obtener_turnos(data.SERVICIO_ID)
    historial_semana_previa = db_queries.cargar_guardias_previas(data.FECHA_INICIO, dias_atras=28, servicio_id=data.SERVICIO_ID)
    offset_dia = 2 # July 1st 2026 is Wednesday
    
    modelo, turnos, flr_tracker, vars_turno_sem = main.construir_modelo(
        empleados, config_turnos, turnos_dict, demanda_req, adjustments,
        31, [8], offset_dia, 5, reglas_servicio_db, ajustes_reglas,
        historial_semana_previa, data.SERVICIO_ID
    )
    
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 8
    status = solver.Solve(modelo)
    
    os.remove("scratch/soft_rules_temp.py")
    return status == cp_model.OPTIMAL or status == cp_model.FEASIBLE

rules_to_test = [
    "MIN_DIA_ESPECIFICO_MES",
    "PESO_INCONSISTENCIA",
    "BONUS_COMBO_FINDE",
    "PESO_MIX_HORARIO",
    "PREFERENCIAS",
    "FINDE_LARGO_REGLAMENTARIO",
    "OBJETIVO_ROTACION_MENSUAL",
    "PENALIZACION_TURNO_AUSENTE",
    "BONUS_POR_CARGA_PERFECTA",
    "PESO_EQUIDAD_FERIADOS",
    "PESO_BRECHA_DIARIA_PERSONAL",
    "PESO_EQUIDAD_FINDES_MENSUAL",
    "PESO_EQUIDAD_FINDES_ANUAL",
    "PESO_BRECHA_MENSUAL",
    "PESO_BRECHA_ANUAL",
    "PESO_BRECHA_SEMANAL_SEGUIMIENTO",
    "PESO_BRECHA_MENSUAL_CALENDARIO",
    "PESO_EQUIDAD_FINDES_MENSUAL_CALENDARIO",
    "PESO_EQUIDAD_FL3",
    "PESO_EQUIDAD_FL4"
]

print("=== DIAGNOSING INDIVIDUAL SOFT RULES ===")
for rule in rules_to_test:
    res = run_test(rule)
    print(f"Disable rule {rule:<40} -> {'FACTIBLE' if res else 'INVIABLE'}")
