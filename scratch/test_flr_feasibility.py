import sys
import os
from datetime import datetime, date

# Ensure root is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import construir_modelo
from database import queries as db_queries
from database import schema as db_schema
from database.data_loader import obtener_empleados, obtener_turnos
from ortools.sat.python import cp_model

def run_test():
    servicio_id = 2
    fecha_inicio = "2026-07-01"
    fecha_fin = "2026-07-31"
    
    db_schema.inicializar_db()
    db_queries.init_licencias()
    
    fecha_inicio_dt = datetime.strptime(fecha_inicio, "%Y-%m-%d")
    fecha_fin_dt    = datetime.strptime(fecha_fin,    "%Y-%m-%d")
    
    total_dias = (fecha_fin_dt - fecha_inicio_dt).days + 1
    DIAS_DEL_BLOQUE = total_dias
    num_semanas     = (DIAS_DEL_BLOQUE + 6) // 7

    feriados_indices = []
    feriados_db = db_queries.obtener_feriados(fecha_inicio, fecha_fin)
    for f_str in feriados_db:
        f_dt = datetime.strptime(f_str, "%Y-%m-%d")
        delta = (f_dt - fecha_inicio_dt).days
        if 0 <= delta < DIAS_DEL_BLOQUE:
            feriados_indices.append(delta)

    config_turnos, metadata_turnos_raw, demanda_req, ajustes_db = db_queries.cargar_configuracion_turnos(
        servicio_id=servicio_id, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin
    )
    reglas_servicio_db = db_queries.cargar_reglas_servicio(servicio_id)
    ajustes_reglas = db_queries.cargar_ajustes_reglas_personal(fecha_inicio, fecha_fin)
    
    ajustes_servicio = db_queries.cargar_ajustes_reglas_servicio(fecha_inicio, fecha_fin, servicio_id)
    ajustes_reglas['__servicio__'] = ajustes_servicio
    
    empleados = obtener_empleados(servicio_id, fecha_inicio, DIAS_DEL_BLOQUE)
    turnos_dict = obtener_turnos(servicio_id)
    
    historial_semana_previa = db_queries.cargar_guardias_previas(fecha_inicio, dias_atras=28, servicio_id=servicio_id)
    offset_dia = fecha_inicio_dt.weekday()
    
    # Build model (with modo_debug=True so we can see violations)
    modelo, turnos, flr_tracker, ctx = construir_modelo(
        empleados, config_turnos, turnos_dict, demanda_req, ajustes_db,
        DIAS_DEL_BLOQUE, feriados_indices, offset_dia, num_semanas,
        reglas_servicio=reglas_servicio_db,
        ajustes_reglas_personal=ajustes_reglas,
        historial_semana_previa=historial_semana_previa,
        servicio_id=servicio_id,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        modo_debug=True
    )
    
    # Now, let's force FLR for BORIA MAYRA!
    # How is FLR tracked? In flr_tracker: dict of (nombre, d) -> var
    # Let's find all FLR variables for BORIA MAYRA
    boria_flr_vars = [var for (nombre, d), var in flr_tracker.items() if nombre == 'BORIA MAYRA']
    print(f"Found {len(boria_flr_vars)} FLR candidate variables for BORIA MAYRA.")
    
    if boria_flr_vars:
        # Force that at least one FLR must be true (sum(vars) >= 1)
        # We wrap this in an assumption for the debugger to see if it is the culprit
        nombre_assume = "REG_FORCE_FLR_BORIA"
        b_assume = modelo.NewBoolVar(nombre_assume)
        ctx.assumptions.append((nombre_assume, b_assume))
        modelo.Add(sum(boria_flr_vars) >= 1).OnlyEnforceIf(b_assume)
        print("Forced FLR for BORIA MAYRA under assumption REG_FORCE_FLR_BORIA.")
    else:
        print("No FLR candidate variables found for BORIA MAYRA!")

    # Let's also force FLR for ALL other employees to see if it's feasible
    # We can create a separate assumption for each employee's FLR
    # for emp in empleados:
    #     emp_vars = [var for (nombre, d), var in flr_tracker.items() if nombre == emp.nombre]
    #     if emp_vars and emp.nombre != 'BORIA MAYRA':
    #         # Create assumption
    #         as_name = f"REG_FORCE_FLR_{emp.nombre.replace(' ', '_')}"
    #         var_assume = modelo.NewBoolVar(as_name)
    #         ctx.assumptions.append((as_name, var_assume))
    #         modelo.Add(sum(emp_vars) >= 1).OnlyEnforceIf(var_assume)
            
    # Solve
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 100
    solver.parameters.num_search_workers = 8
    
    # We need to activate assumptions before solve
    from restricciones.cargador import activar_assumptions, reportar_conflicto
    activar_assumptions(modelo, ctx)
    
    print("Solving with forced FLR restrictions...")
    status = solver.Solve(modelo)
    
    print("Status:", solver.StatusName(status))
    if status == cp_model.INFEASIBLE:
        reportar_conflicto(solver, ctx)
    elif status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        print("Feasible! FLR can be given to BORIA MAYRA and others.")
        # Print who gets FLR
        for (nombre, d), var in flr_tracker.items():
            if solver.Value(var) == 1:
                print(f"  FLR assigned: {nombre} starting on day {d}")
        # Print guardias for BORIA MAYRA
        print("Guardias assigned to BORIA MAYRA in debug solution:")
        for d_idx in range(DIAS_DEL_BLOQUE):
            for t in turnos_dict.keys():
                if ('BORIA MAYRA', d_idx, t) in turnos and solver.Value(turnos[('BORIA MAYRA', d_idx, t)]) == 1:
                    print(f"  Day {d_idx+1}: {t}")
        # Print debug violations
        if ctx.modo_debug:
            infracciones = []
            for peso, var in ctx.penalizaciones:
                if solver.Value(var) == 1:
                    parts = var.Name().split("__")
                    codigo_regla = parts[1] if len(parts) > 1 else "DESCONOCIDA"
                    etiqueta = "__".join(parts[2:]) if len(parts) > 2 else ""
                    infracciones.append((codigo_regla, etiqueta))
            print(f"--- DIAGNÓSTICO DEBUG: Se detectaron {len(infracciones)} infracciones de reglas ---")
            for cod, et in infracciones:
                print(f"  VIOLATION: {cod} on {et}")

if __name__ == "__main__":
    run_test()
