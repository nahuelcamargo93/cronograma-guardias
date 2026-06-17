import sys
import os
import shutil
import sqlite3
import json
sys.path.append(os.path.abspath('.'))

import datetime
import pandas as pd
from ortools.sat.python import cp_model

# Copiar base de datos para evitar bloqueos
db_orig = 'cronograma_inteligente.db'
db_copy = 'cronograma_inteligente_diagnose.db'
try:
    shutil.copy2(db_orig, db_copy)
except Exception as e:
    print(f"Error al copiar base de datos: {e}")
    sys.exit(1)

# Conectarse a la copia e aplicar todas las suspensiones
try:
    conn = sqlite3.connect(db_copy)
    cursor = conn.cursor()
    
    # Ajustes de servicio
    ajustes_serv = [
        (1, 'MAX_HORAS_MES_CALENDARIO', '2026-06-22', '2026-06-30', 'SUSPENDER', None, 1),
        (1, 'MIN_HORAS_MES_CALENDARIO', '2026-06-22', '2026-06-30', 'SUSPENDER', None, 1),
        (1, 'MAX_HORAS_SEMANA', '2026-06-22', '2026-06-30', 'SOBRESCRIBIR', json.dumps({"limite": 36}), 1)
    ]
    for s_id, cod, fi, ff, acc, params, act in ajustes_serv:
        cursor.execute("""
            DELETE FROM servicios_reglas_ajustes
            WHERE servicio_id = ? AND codigo_regla = ? AND fecha_inicio = ? AND fecha_fin = ?
        """, (s_id, cod, fi, ff))
        cursor.execute("""
            INSERT INTO servicios_reglas_ajustes (servicio_id, codigo_regla, fecha_inicio, fecha_fin, accion, parametros_json, activo)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (s_id, cod, fi, ff, acc, params, act))
        
    # Ajuste individual para Giacoppo Veronica
    cursor.execute("""
        DELETE FROM personal_reglas_ajustes
        WHERE personal_nombre = 'Giacoppo, Veronica' AND codigo_regla = 'SEMANAS_SEGUIMIENTO_REQUERIDAS' AND fecha_inicio = '2026-06-22' AND fecha_fin = '2026-06-30'
    """)
    cursor.execute("""
        INSERT INTO personal_reglas_ajustes (personal_nombre, codigo_regla, fecha_inicio, fecha_fin, accion, activo)
        VALUES ('Giacoppo, Veronica', 'SEMANAS_SEGUIMIENTO_REQUERIDAS', '2026-06-22', '2026-06-30', 'SUSPENDER', 1)
    """)
    
    conn.commit()
    conn.close()
    print("Ajustes simulados con éxito en la base de datos temporal.")
except Exception as e:
    print(f"Error al aplicar ajustes en la base de datos de prueba: {e}")
    sys.exit(1)

# Mono-patchear DB_PATH en el módulo connection
import database.connection as db_conn
db_conn.DB_PATH = os.path.abspath(db_copy)

from database import queries as db_queries
from database import schema as db_schema
from database.data_loader import obtener_empleados, obtener_turnos
from main import construir_modelo, resolver_modelo

def main():
    servicio_id = 1
    fecha_inicio = "2026-06-22"
    fecha_fin = "2026-06-30"
    
    fecha_inicio_dt = datetime.datetime.strptime(fecha_inicio, "%Y-%m-%d")
    fecha_fin_dt    = datetime.datetime.strptime(fecha_fin,    "%Y-%m-%d")
    total_dias = (fecha_fin_dt - fecha_inicio_dt).days + 1
    
    lunes_unicos = set()
    for d in range(total_dias):
        fecha_d = fecha_inicio_dt + datetime.timedelta(days=d)
        lunes = fecha_d - datetime.timedelta(days=fecha_d.weekday())
        lunes_unicos.add(lunes.date())
    num_semanas = len(lunes_unicos)

    feriados_indices = []
    feriados_db = db_queries.obtener_feriados(fecha_inicio, fecha_fin, servicio_id=servicio_id)
    for f_str in feriados_db:
        f_dt = datetime.datetime.strptime(f_str, "%Y-%m-%d")
        delta = (f_dt - fecha_inicio_dt).days
        if 0 <= delta < total_dias:
            feriados_indices.append(delta)

    config_turnos, metadata_turnos_raw, demanda_req, ajustes_db = db_queries.cargar_configuracion_turnos(
        servicio_id=servicio_id, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin
    )
    reglas_servicio_db = db_queries.cargar_reglas_servicio(servicio_id)
    ajustes_reglas = db_queries.cargar_ajustes_reglas_personal(fecha_inicio, fecha_fin)
    ajustes_servicio = db_queries.cargar_ajustes_reglas_servicio(fecha_inicio, fecha_fin, servicio_id)
    ajustes_reglas['__servicio__'] = ajustes_servicio
    
    empleados = obtener_empleados(servicio_id, fecha_inicio, total_dias)
    turnos_dict = obtener_turnos(servicio_id)
    historial_semana_previa = db_queries.cargar_guardias_previas(fecha_inicio, dias_atras=28, servicio_id=servicio_id)
    offset_dia = fecha_inicio_dt.weekday()

    # Resolver de forma normal para ver si es viable
    print("--- CORRIENDO OPTIMIZACIÓN NORMAL ---")
    modelo, turnos, flr_tracker, ctx = construir_modelo(
        empleados, config_turnos, turnos_dict, demanda_req, ajustes_db,
        total_dias, feriados_indices, offset_dia, num_semanas,
        reglas_servicio=reglas_servicio_db,
        ajustes_reglas_personal=ajustes_reglas,
        historial_semana_previa=historial_semana_previa,
        servicio_id=servicio_id,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        modo_debug=False
    )
    
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 30
    status = solver.Solve(modelo)
    
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        print("¡LOGRADO! El cronograma es factible con todos los ajustes.")
    else:
        print("Fallo de factibilidad. Estado:", status)

    try:
        os.remove(db_copy)
    except:
        pass

if __name__ == "__main__":
    main()
