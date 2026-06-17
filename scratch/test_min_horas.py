import os
import sys

# Asegurar que la raíz del proyecto está en el path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import datetime
from datetime import date, timedelta
from ortools.sat.python import cp_model
from database import queries as db_queries
from database.data_loader import obtener_empleados, obtener_turnos
from restricciones.contexto import ContextoModelo
from restricciones.cargador import cargar_y_ejecutar_todas
import main as main_module

def main():
    servicio_id = 2
    fecha_inicio = "2026-07-01"
    fecha_fin = "2026-07-31"
    
    fecha_inicio_dt = datetime.datetime.strptime(fecha_inicio, "%Y-%m-%d")
    fecha_fin_dt    = datetime.datetime.strptime(fecha_fin,    "%Y-%m-%d")
    total_dias = (fecha_fin_dt - fecha_inicio_dt).days + 1
    
    # Cargar datos base
    config_turnos, metadata_turnos_raw, demanda_req, ajustes_db = db_queries.cargar_configuracion_turnos(
        servicio_id=servicio_id, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin
    )
    
    # Cargar reglas del servicio
    reglas_servicio_db = db_queries.cargar_reglas_servicio(servicio_id)
    
    # Dejar SOLAMENTE MIN_HORAS_MES_CALENDARIO activa y suspender las demás
    print("Reglas del catálogo encontradas:")
    nuevas_reglas = {}
    for cod_regla, config in reglas_servicio_db.items():
        if cod_regla == "MIN_HORAS_MES_CALENDARIO":
            nuevas_reglas[cod_regla] = config
            print(f"  [ACTIVA] {cod_regla}: {config}")
        else:
            # En lugar de quitar la regla, le ponemos suspendida=True
            # para que apply no lance excepciones de falta de config
            # pero no agregue restricciones.
            if isinstance(config, dict):
                nuevas_config = config.copy()
                nuevas_config['suspendida'] = True
            elif isinstance(config, list):
                # Si es una lista, puede ser que rule_engine maneje una lista vacía o suspendida
                # Le pasamos un dict con suspendida: True
                nuevas_config = {'suspendida': True}
            else:
                nuevas_config = {'suspendida': True}
            nuevas_reglas[cod_regla] = nuevas_config
            print(f"  [SUSPENDIDA] {cod_regla}")
            
    # También pasamos ajustes de reglas vacíos
    ajustes_reglas = {'__servicio__': []}
    
    # Empleados y turnos
    empleados = obtener_empleados(servicio_id, fecha_inicio, total_dias)
    turnos_dict = obtener_turnos(servicio_id)
    
    # Feriados
    feriados_indices = []
    feriados_db = db_queries.obtener_feriados(fecha_inicio, fecha_fin, servicio_id=servicio_id)
    for f_str in feriados_db:
        f_dt = datetime.datetime.strptime(f_str, "%Y-%m-%d")
        delta = (f_dt - fecha_inicio_dt).days
        if 0 <= delta < total_dias:
            feriados_indices.append(delta)
            
    offset_dia = fecha_inicio_dt.weekday()
    
    # Calcular semanas
    lunes_unicos = set()
    for d in range(total_dias):
        fecha_d = fecha_inicio_dt + datetime.timedelta(days=d)
        lunes = fecha_d - datetime.timedelta(days=fecha_d.weekday())
        lunes_unicos.add(lunes.date())
    num_semanas = len(lunes_unicos)
    
    # Construir el modelo
    print("\nConstruyendo modelo en MODO_DEBUG...")
    modelo, turnos, flr_tracker, ctx = main_module.construir_modelo(
        empleados, config_turnos, turnos_dict, demanda_req, ajustes_db,
        total_dias, feriados_indices, offset_dia, num_semanas,
        reglas_servicio=nuevas_reglas,
        ajustes_reglas_personal=ajustes_reglas,
        historial_semana_previa={},
        servicio_id=servicio_id,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        modo_debug=True,       # Habilitar MODO_DEBUG para ver violaciones
        force_assumptions=False
    )
    
    # Resolver
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 30
    solver.parameters.num_search_workers = 4
    status = solver.Solve(modelo)
    
    print(f"Estado de la resolución: {solver.StatusName(status)}")
    
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        infracciones = []
        for peso, var in ctx.penalizaciones:
            if solver.Value(var) == 1:
                parts = var.Name().split("__")
                codigo_regla = parts[1] if len(parts) > 1 else "DESCONOCIDA"
                etiqueta = "__".join(parts[2:]) if len(parts) > 2 else ""
                infracciones.append((codigo_regla, etiqueta))
        
        if infracciones:
            print(f"\n--- SE DETECTARON {len(infracciones)} INFRACCIONES ---")
            for cod, et in infracciones:
                print(f"  Regla: {cod} | Detalle: {et}")
        else:
            print("\nModelo viable! No hay infracciones.")
    else:
        print("Incluso en MODO_DEBUG no se pudo resolver.")
            
if __name__ == "__main__":
    main()
