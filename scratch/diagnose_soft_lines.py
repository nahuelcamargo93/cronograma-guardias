import sys
import os
import shutil
import subprocess

def test_modified_soft_rules(disabled_blocks):
    # Copy original soft_rules.py to a temp file
    shutil.copy("soft_rules.py", "soft_rules_backup.py")
    
    try:
        with open("soft_rules.py", "r", encoding="utf-8") as f:
            content = f.read()
            
        # Selectively disable blocks by replacing key lines with comments or pass
        if "min_dia_especifico" in disabled_blocks:
            content = content.replace(
                "_aplicar_min_dia_especifico_mes_soft(modelo, turnos, empleados, turnos_dict, reglas_servicio, ajustes_personal, dias_del_bloque, fecha_inicio_dt, penalizaciones_ad_hoc, servicio_id)",
                "pass # disabled min_dia_especifico"
            )
            
        if "penalizacion_turno" in disabled_blocks:
            # We can mock PENALIZACION_TURNO inside loop
            content = content.replace(
                "params_penal_turno = rule_engine.resolver_parametros_regla('PENALIZACION_TURNO', nombre, FECHA_INICIO, reglas_servicio, emp.reglas, ajustes_personal)",
                "params_penal_turno = None # disabled penalizacion_turno"
            )
            
        if "brechas" in disabled_blocks:
            # Disable brecha mensual, anual, seg
            content = content.replace(
                "modelo.Add(total_mes <= max_horas_mes)", "pass"
            ).replace(
                "modelo.Add(total_mes >= min_horas_mes)", "pass"
            ).replace(
                "modelo.Add(total_anual_proyectado <= max_anual)", "pass"
            ).replace(
                "modelo.Add(total_anual_proyectado >= min_anual)", "pass"
            ).replace(
                "modelo.Add(total_seg_proyectado <= max_seg)", "pass"
            ).replace(
                "modelo.Add(total_seg_proyectado >= min_seg)", "pass"
            )
            
        if "flr" in disabled_blocks:
            content = content.replace(
                "active_flr_rule = ('normal', params_flr)", "active_flr_rule = None"
            ).replace(
                "active_flr_rule = ('estricto', params_flr_estricto)", "active_flr_rule = None"
            )
            
        if "equidad_fl" in disabled_blocks:
            content = content.replace(
                "modelo.Add(total_fl3 <= max_fl3)", "pass"
            ).replace(
                "modelo.Add(total_fl3 >= min_fl3)", "pass"
            ).replace(
                "modelo.Add(total_fl4 <= max_fl4)", "pass"
            ).replace(
                "modelo.Add(total_fl4 >= min_fl4)", "pass"
            )
            
        if "equidad_feriados" in disabled_blocks:
            content = content.replace(
                "modelo.Add(total_feriados <= max_feriados)", "pass"
            ).replace(
                "modelo.Add(total_feriados >= min_feriados)", "pass"
            )
            
        if "objetivo_rotacion" in disabled_blocks:
            content = content.replace(
                "modelo.AddAbsEquality(diff, total_t - target)", "pass"
            )
            
        if "diversidad" in disabled_blocks:
            content = content.replace(
                "modelo.Add(sum(sem_vars) >= 1).OnlyEnforceIf(has_f)", "pass"
            ).replace(
                "modelo.Add(sum(sem_vars) == 0).OnlyEnforceIf(has_f.Not())", "pass"
            )
            
        if "carga_perfecta" in disabled_blocks:
            content = content.replace(
                "modelo.Add(total_h_mes_var >= min_h).OnlyEnforceIf(b_perfect)", "pass"
            ).replace(
                "modelo.Add(total_h_mes_var <= max_h).OnlyEnforceIf(b_perfect)", "pass"
            )
            
        with open("soft_rules.py", "w", encoding="utf-8") as f:
            f.write(content)
            
        # Run check_solve_status.py
        result = subprocess.run(["python", "scratch/check_solve_status.py"], capture_output=True, text=True)
        return "Model solved successfully!" in result.stdout
        
    finally:
        # Restore backup
        shutil.copy("soft_rules_backup.py", "soft_rules.py")
        os.remove("soft_rules_backup.py")

blocks_to_test = [
    "min_dia_especifico",
    "penalizacion_turno",
    "brechas",
    "flr",
    "equidad_fl",
    "equidad_feriados",
    "objetivo_rotacion",
    "diversidad",
    "carga_perfecta"
]

print("Testing deactivating blocks one by one...")
for block in blocks_to_test:
    if test_modified_soft_rules([block]):
        print(f"--> [SUCCESS] Model becomes FEASIBLE when disabling block: {block}")
    else:
        print(f"Disabling block '{block}' does not resolve infeasibility.")

print("\nTesting deactivating combinations of blocks...")
import itertools
for r in range(2, 4):
    for comb in itertools.combinations(blocks_to_test, r):
        if test_modified_soft_rules(comb):
            print(f"--> [SUCCESS] Model becomes FEASIBLE when disabling combo: {comb}")
            sys.exit(0)
