import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import datetime
from database import queries as db_queries
from database.data_loader import obtener_empleados, obtener_turnos
from main import construir_modelo, resolver_modelo

def run_test():
    servicio_id = 2
    fecha_inicio = "2026-07-01"
    fecha_fin = "2026-07-31"

    fecha_inicio_dt = datetime.datetime.strptime(fecha_inicio, "%Y-%m-%d")
    fecha_fin_dt    = datetime.datetime.strptime(fecha_fin,    "%Y-%m-%d")
    total_dias = (fecha_fin_dt - fecha_inicio_dt).days + 1
    num_semanas     = (total_dias + 6) // 7

    feriados_indices = []
    feriados_db = db_queries.obtener_feriados(fecha_inicio, fecha_fin)
    for f_str in feriados_db:
        f_dt = datetime.datetime.strptime(f_str, "%Y-%m-%d")
        delta = (f_dt - fecha_inicio_dt).days
        if 0 <= delta < total_dias:
            feriados_indices.append(delta)

    config_turnos, turnos_dict_raw, demanda_req, ajustes_db = db_queries.cargar_configuracion_turnos(
        servicio_id=servicio_id, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin
    )
    reglas_servicio_db = db_queries.cargar_reglas_servicio(servicio_id)

    # Aseguramos que MAX_FRANCOS_CONTINUOS está configurada en la DB
    print("Reglas cargadas de la DB para el servicio 2:")
    for k, v in reglas_servicio_db.items():
        if k in ('MAX_FRANCOS_SEMANA', 'MAX_FRANCOS_CONTINUOS'):
            print(f"  - {k}: {v}")

    ajustes_reglas = db_queries.cargar_ajustes_reglas_personal(fecha_inicio, fecha_fin)
    ajustes_servicio = db_queries.cargar_ajustes_reglas_servicio(fecha_inicio, fecha_fin, servicio_id)
    ajustes_reglas['__servicio__'] = ajustes_servicio

    empleados = obtener_empleados(servicio_id, fecha_inicio, total_dias)
    turnos_dict = obtener_turnos(servicio_id)
    historial_semana_previa = db_queries.cargar_guardias_previas(fecha_inicio, dias_atras=28, servicio_id=servicio_id)
    offset_dia = fecha_inicio_dt.weekday()

    # Comprobar la regla para POLETTI NATALIA
    for emp in empleados:
        if emp.nombre == 'POLETTI NATALIA':
            print(f"\nReglas cargadas para POLETTI NATALIA: {emp.reglas.keys()}")
            print(f"Parámetros de MAX_FRANCOS_CONTINUOS para ella: {emp.reglas.get('MAX_FRANCOS_CONTINUOS')}")

    print("\nConstruyendo modelo...")
    modelo, turnos, flr_tracker, ctx = construir_modelo(
        empleados, config_turnos, turnos_dict, demanda_req, ajustes_db,
        total_dias, feriados_indices, offset_dia, num_semanas,
        reglas_servicio=reglas_servicio_db,
        ajustes_reglas_personal=ajustes_reglas,
        historial_semana_previa=historial_semana_previa,
        servicio_id=servicio_id,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        modo_debug=False,
        force_assumptions=False
    )

    print("\nResolviendo modelo...")
    res = resolver_modelo(
        modelo, turnos, flr_tracker, empleados, total_dias, feriados_indices,
        fecha_inicio, offset_dia, config_turnos, ctx, max_time_in_seconds=30
    )

    if res[0] is not None:
        df_resultados, flrs_asignados, df_cat_semanas, infracciones = res
        print("\n¡Modelo resuelto con éxito!")
        print(f"Total asignaciones: {len(df_resultados)}")

        # Verificar secuencias de francos consecutivas para cada empleado
        import pandas as pd
        df = df_resultados
        
        # Mapeamos a un formato fácil: empleado -> lista de booleanos indicando si trabajó cada día
        # df tiene columnas: 'fecha', 'nombre', 'turno', 'horas'
        trabajo_emp = {}
        for emp in empleados:
            trabajo_emp[emp.nombre] = [False] * total_dias
            
        for _, row in df.iterrows():
            nombre = row['nombre']
            fecha_str = row['fecha']
            # Obtener índice de día
            f_dt = datetime.datetime.strptime(fecha_str, "%Y-%m-%d")
            d_idx = (f_dt - fecha_inicio_dt).days
            if 0 <= d_idx < total_dias:
                # Si trabajó un turno real y no es un "libre"
                if row['turno'] not in ('L', 'FRANCO', 'Franco', 'Libre', 'LI', 'LC'):
                    trabajo_emp[nombre][d_idx] = True

        print("\nAnálisis de Francos Consecutivos en el Cronograma Solucionado:")
        for emp in empleados:
            nombre = emp.nombre
            dias_lic = emp.dias_licencia
            
            # Construir la lista de franco real excluyendo licencias
            es_franco = []
            for d in range(total_dias):
                if d in dias_lic:
                    es_franco.append(False)  # Licencia no es franco real
                else:
                    es_franco.append(not trabajo_emp[nombre][d])
            
            # Calcular rachas de franco consecutivos
            max_racha = 0
            racha_actual = 0
            for val in es_franco:
                if val:
                    racha_actual += 1
                    if racha_actual > max_racha:
                        max_racha = racha_actual
                else:
                    racha_actual = 0
                    
            print(f"  * {nombre}: Max francos seguidos = {max_racha} (Licencias: {len(dias_lic)} días)")
            
            # Si no es POLETTI NATALIA, el límite debería ser <= 3 (si está en HARD)
            if nombre != 'POLETTI NATALIA':
                if max_racha > 3:
                    print(f"    [FALLO] {nombre} superó el límite de 3 francos consecutivos ({max_racha} francos)!")
                else:
                    print(f"    [OK] Respeta el límite.")
            else:
                print(f"    [INFO] POLETTI NATALIA (regla suspendida) tiene max racha = {max_racha}.")
    else:
        print("\n[FALLO] No se pudo resolver el modelo.")

if __name__ == "__main__":
    run_test()
