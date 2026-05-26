import sys
import os
import shutil
from ortools.sat.python import cp_model

sys.path.append(os.getcwd())

import data
import main
from database import queries as db_queries
from database.data_loader import obtener_empleados, obtener_turnos

# Load data once
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

def run_variation(variation_code):
    shutil.copy("soft_rules.py", "scratch/soft_rules_temp.py")
    
    with open("scratch/soft_rules_temp.py", "r", encoding="utf-8") as f:
        content = f.read()
        
    content = content.replace(
        'print(f"DEBUG: Penalizando {nombre} dia {d} turno {t_a_penalizar} peso {peso} es_f={es_f}")',
        'pass # print(...)'
    )

    # We will replace the entire BONUS POR CARGA PERFECTA block with a custom variation
    # Let's target from "# --- BONUS POR CARGA PERFECTA ---" to "puntos_bonus.append(b_perfect * bonus_val)"
    # We can write a replacement that matches this range.
    
    target_block = """        # --- BONUS POR CARGA PERFECTA ---
        params_bonus = rule_engine.resolver_parametros_regla('BONUS_POR_CARGA_PERFECTA', nombre, FECHA_INICIO, reglas_servicio, emp.reglas, ajustes_personal)
        if rule_engine.regla_existe(params_bonus) and not rule_engine.regla_suspendida(params_bonus) and turnos_dict:
            min_h = params_bonus.get('min_h', 142)
            max_h = params_bonus.get('max_h', 146)
            bonus_val = params_bonus.get('bonus', 2000)
            
            meses_en_bloque = {}
            fecha_inicio_dt = date.fromisoformat(FECHA_INICIO)
            for d in range(dias_del_bloque):
                m_key = (fecha_inicio_dt + timedelta(days=d)).strftime("%Y-%m")
                meses_en_bloque.setdefault(m_key, []).append(d)
            
            for m_key, dias_m in meses_en_bloque.items():
                h_vars_m = []
                for d in dias_m:
                    es_f = ((d + offset_dia) % 7) >= 5 or d in feriados
                    tipo_dia_h = "Finde_Feriado" if es_f else "Semana"
                    for t in demanda_turnos.get(tipo_dia_h, {}).keys():
                        if (nombre, d, t) in turnos:
                            h_t = turnos_dict[t].horas if t in turnos_dict else 6
                            h_vars_m.append(turnos[(nombre, d, t)] * h_t)
                
                # Licencias pro-rata
                dias_lic_m = [d for d in dias_m if d in dias_bloqueados_persona]
                val_dia = 144.0 / dias_del_bloque
                h_lic_m = int(val_dia * len(dias_lic_m) + 0.5)
                
                total_h_mes_var = modelo.NewIntVar(0, 500, f'h_mes_{nombre}_{m_key}')
                modelo.Add(total_h_mes_var == sum(h_vars_m) + h_lic_m)
                
                b_perfect = modelo.NewBoolVar(f'b_perfect_{nombre}_{m_key}')
                b_high = modelo.NewBoolVar(f'b_high_{nombre}_{m_key}')
                b_low = modelo.NewBoolVar(f'b_low_{nombre}_{m_key}')
                
                modelo.Add(total_h_mes_var >= min_h).OnlyEnforceIf(b_high)
                modelo.Add(total_h_mes_var < min_h).OnlyEnforceIf(b_high.Not())
                modelo.Add(total_h_mes_var <= max_h).OnlyEnforceIf(b_low)
                modelo.Add(total_h_mes_var > max_h).OnlyEnforceIf(b_low.Not())
                
                modelo.AddBoolAnd([b_high, b_low]).OnlyEnforceIf(b_perfect)
                modelo.AddBoolOr([b_high.Not(), b_low.Not()]).OnlyEnforceIf(b_perfect.Not())
                
                puntos_bonus.append(b_perfect * bonus_val)"""

    if target_block not in content:
        # Let's try with different line endings or slightly different indentation
        # We can search for a smaller subset. Let's do a substring match.
        print("ERROR: target_block not found in soft_rules.py!")
        sys.exit(1)

    replacement = ""
    if variation_code == 1:
        # Only define total_h_mes_var
        replacement = """        # --- BONUS POR CARGA PERFECTA ---
        params_bonus = rule_engine.resolver_parametros_regla('BONUS_POR_CARGA_PERFECTA', nombre, FECHA_INICIO, reglas_servicio, emp.reglas, ajustes_personal)
        if rule_engine.regla_existe(params_bonus) and not rule_engine.regla_suspendida(params_bonus) and turnos_dict:
            min_h = params_bonus.get('min_h', 142)
            max_h = params_bonus.get('max_h', 146)
            bonus_val = params_bonus.get('bonus', 2000)
            meses_en_bloque = {}
            fecha_inicio_dt = date.fromisoformat(FECHA_INICIO)
            for d in range(dias_del_bloque):
                m_key = (fecha_inicio_dt + timedelta(days=d)).strftime("%Y-%m")
                meses_en_bloque.setdefault(m_key, []).append(d)
            for m_key, dias_m in meses_en_bloque.items():
                h_vars_m = []
                for d in dias_m:
                    es_f = ((d + offset_dia) % 7) >= 5 or d in feriados
                    tipo_dia_h = "Finde_Feriado" if es_f else "Semana"
                    for t in demanda_turnos.get(tipo_dia_h, {}).keys():
                        if (nombre, d, t) in turnos:
                            h_t = turnos_dict[t].horas if t in turnos_dict else 6
                            h_vars_m.append(turnos[(nombre, d, t)] * h_t)
                dias_lic_m = [d for d in dias_m if d in dias_bloqueados_persona]
                val_dia = 144.0 / dias_del_bloque
                h_lic_m = int(val_dia * len(dias_lic_m) + 0.5)
                total_h_mes_var = modelo.NewIntVar(0, 500, f'h_mes_{nombre}_{m_key}')
                modelo.Add(total_h_mes_var == sum(h_vars_m) + h_lic_m)"""
    elif variation_code == 2:
        # Define total_h_mes_var and boolean variables (but no implications)
        replacement = """        # --- BONUS POR CARGA PERFECTA ---
        params_bonus = rule_engine.resolver_parametros_regla('BONUS_POR_CARGA_PERFECTA', nombre, FECHA_INICIO, reglas_servicio, emp.reglas, ajustes_personal)
        if rule_engine.regla_existe(params_bonus) and not rule_engine.regla_suspendida(params_bonus) and turnos_dict:
            min_h = params_bonus.get('min_h', 142)
            max_h = params_bonus.get('max_h', 146)
            bonus_val = params_bonus.get('bonus', 2000)
            meses_en_bloque = {}
            fecha_inicio_dt = date.fromisoformat(FECHA_INICIO)
            for d in range(dias_del_bloque):
                m_key = (fecha_inicio_dt + timedelta(days=d)).strftime("%Y-%m")
                meses_en_bloque.setdefault(m_key, []).append(d)
            for m_key, dias_m in meses_en_bloque.items():
                h_vars_m = []
                for d in dias_m:
                    es_f = ((d + offset_dia) % 7) >= 5 or d in feriados
                    tipo_dia_h = "Finde_Feriado" if es_f else "Semana"
                    for t in demanda_turnos.get(tipo_dia_h, {}).keys():
                        if (nombre, d, t) in turnos:
                            h_t = turnos_dict[t].horas if t in turnos_dict else 6
                            h_vars_m.append(turnos[(nombre, d, t)] * h_t)
                dias_lic_m = [d for d in dias_m if d in dias_bloqueados_persona]
                val_dia = 144.0 / dias_del_bloque
                h_lic_m = int(val_dia * len(dias_lic_m) + 0.5)
                total_h_mes_var = modelo.NewIntVar(0, 500, f'h_mes_{nombre}_{m_key}')
                modelo.Add(total_h_mes_var == sum(h_vars_m) + h_lic_m)
                b_high = modelo.NewBoolVar(f'b_high_{nombre}_{m_key}')
                b_low = modelo.NewBoolVar(f'b_low_{nombre}_{m_key}')"""
    elif variation_code == 3:
        # Define total_h_mes_var and boolean variables with implications (but no b_perfect)
        replacement = """        # --- BONUS POR CARGA PERFECTA ---
        params_bonus = rule_engine.resolver_parametros_regla('BONUS_POR_CARGA_PERFECTA', nombre, FECHA_INICIO, reglas_servicio, emp.reglas, ajustes_personal)
        if rule_engine.regla_existe(params_bonus) and not rule_engine.regla_suspendida(params_bonus) and turnos_dict:
            min_h = params_bonus.get('min_h', 142)
            max_h = params_bonus.get('max_h', 146)
            bonus_val = params_bonus.get('bonus', 2000)
            meses_en_bloque = {}
            fecha_inicio_dt = date.fromisoformat(FECHA_INICIO)
            for d in range(dias_del_bloque):
                m_key = (fecha_inicio_dt + timedelta(days=d)).strftime("%Y-%m")
                meses_en_bloque.setdefault(m_key, []).append(d)
            for m_key, dias_m in meses_en_bloque.items():
                h_vars_m = []
                for d in dias_m:
                    es_f = ((d + offset_dia) % 7) >= 5 or d in feriados
                    tipo_dia_h = "Finde_Feriado" if es_f else "Semana"
                    for t in demanda_turnos.get(tipo_dia_h, {}).keys():
                        if (nombre, d, t) in turnos:
                            h_t = turnos_dict[t].horas if t in turnos_dict else 6
                            h_vars_m.append(turnos[(nombre, d, t)] * h_t)
                dias_lic_m = [d for d in dias_m if d in dias_bloqueados_persona]
                val_dia = 144.0 / dias_del_bloque
                h_lic_m = int(val_dia * len(dias_lic_m) + 0.5)
                total_h_mes_var = modelo.NewIntVar(0, 500, f'h_mes_{nombre}_{m_key}')
                modelo.Add(total_h_mes_var == sum(h_vars_m) + h_lic_m)
                b_high = modelo.NewBoolVar(f'b_high_{nombre}_{m_key}')
                b_low = modelo.NewBoolVar(f'b_low_{nombre}_{m_key}')
                modelo.Add(total_h_mes_var >= min_h).OnlyEnforceIf(b_high)
                modelo.Add(total_h_mes_var < min_h).OnlyEnforceIf(b_high.Not())
                modelo.Add(total_h_mes_var <= max_h).OnlyEnforceIf(b_low)
                modelo.Add(total_h_mes_var > max_h).OnlyEnforceIf(b_low.Not())"""
    elif variation_code == 4:
        # All implications and b_perfect definition (but no objective term)
        replacement = """        # --- BONUS POR CARGA PERFECTA ---
        params_bonus = rule_engine.resolver_parametros_regla('BONUS_POR_CARGA_PERFECTA', nombre, FECHA_INICIO, reglas_servicio, emp.reglas, ajustes_personal)
        if rule_engine.regla_existe(params_bonus) and not rule_engine.regla_suspendida(params_bonus) and turnos_dict:
            min_h = params_bonus.get('min_h', 142)
            max_h = params_bonus.get('max_h', 146)
            bonus_val = params_bonus.get('bonus', 2000)
            meses_en_bloque = {}
            fecha_inicio_dt = date.fromisoformat(FECHA_INICIO)
            for d in range(dias_del_bloque):
                m_key = (fecha_inicio_dt + timedelta(days=d)).strftime("%Y-%m")
                meses_en_bloque.setdefault(m_key, []).append(d)
            for m_key, dias_m in meses_en_bloque.items():
                h_vars_m = []
                for d in dias_m:
                    es_f = ((d + offset_dia) % 7) >= 5 or d in feriados
                    tipo_dia_h = "Finde_Feriado" if es_f else "Semana"
                    for t in demanda_turnos.get(tipo_dia_h, {}).keys():
                        if (nombre, d, t) in turnos:
                            h_t = turnos_dict[t].horas if t in turnos_dict else 6
                            h_vars_m.append(turnos[(nombre, d, t)] * h_t)
                dias_lic_m = [d for d in dias_m if d in dias_bloqueados_persona]
                val_dia = 144.0 / dias_del_bloque
                h_lic_m = int(val_dia * len(dias_lic_m) + 0.5)
                total_h_mes_var = modelo.NewIntVar(0, 500, f'h_mes_{nombre}_{m_key}')
                modelo.Add(total_h_mes_var == sum(h_vars_m) + h_lic_m)
                b_high = modelo.NewBoolVar(f'b_high_{nombre}_{m_key}')
                b_low = modelo.NewBoolVar(f'b_low_{nombre}_{m_key}')
                modelo.Add(total_h_mes_var >= min_h).OnlyEnforceIf(b_high)
                modelo.Add(total_h_mes_var < min_h).OnlyEnforceIf(b_high.Not())
                modelo.Add(total_h_mes_var <= max_h).OnlyEnforceIf(b_low)
                modelo.Add(total_h_mes_var > max_h).OnlyEnforceIf(b_low.Not())
                b_perfect = modelo.NewBoolVar(f'b_perfect_{nombre}_{m_key}')
                modelo.AddBoolAnd([b_high, b_low]).OnlyEnforceIf(b_perfect)
                modelo.AddBoolOr([b_high.Not(), b_low.Not()]).OnlyEnforceIf(b_perfect.Not())"""

    content = content.replace(target_block, replacement)

    with open("scratch/soft_rules_temp.py", "w", encoding="utf-8") as f:
        f.write(content)
        
    if "scratch.soft_rules_temp" in sys.modules:
        del sys.modules["scratch.soft_rules_temp"]
    import scratch.soft_rules_temp as soft_rules_temp
    
    main.aplicar_reglas_blandas = soft_rules_temp.aplicar_reglas_blandas
    
    # Build model
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

print("=== RUNNING LINE-BY-LINE VARIATIONS ===")
for v in range(1, 5):
    is_ok = run_variation(v)
    print(f"Variation {v}: {'FACTIBLE' if is_ok else 'INVIABLE'}")
