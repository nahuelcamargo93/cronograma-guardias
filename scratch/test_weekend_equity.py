import os
import sys
import datetime
from datetime import date, timedelta
import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import queries as db_queries
from database import schema as db_schema
from database.data_loader import obtener_empleados, obtener_turnos
from main import construir_modelo, resolver_modelo

def test_june_with_equity():
    db_schema.inicializar_db()
    db_queries.init_licencias()
    
    fecha_inicio = "2026-06-01"
    fecha_fin = "2026-06-30"
    servicio_id = 4
    
    fecha_inicio_dt = datetime.datetime.strptime(fecha_inicio, "%Y-%m-%d")
    fecha_fin_dt    = datetime.datetime.strptime(fecha_fin,    "%Y-%m-%d")
    
    total_dias = (fecha_fin_dt - fecha_inicio_dt).days + 1
    DIAS_DEL_BLOQUE = total_dias
    num_semanas     = (DIAS_DEL_BLOQUE + 6) // 7

    feriados_indices = []
    # Feriados de Junio 2026: 2026-06-15, 2026-06-20
    from data import FERIADOS
    for f_str in FERIADOS:
        f_dt = datetime.datetime.strptime(f_str, "%Y-%m-%d")
        delta = (f_dt - fecha_inicio_dt).days
        if 0 <= delta < DIAS_DEL_BLOQUE:
            feriados_indices.append(delta)

    config_turnos, metadata_turnos_raw, demanda_req, ajustes_db = db_queries.cargar_configuracion_turnos(
        servicio_id=servicio_id, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin
    )
    
    reglas_servicio_db = db_queries.cargar_reglas_servicio(servicio_id)
    
    # In-memory activate weekend equity!
    print("Enabling PESO_EQUIDAD_FINDES_MENSUAL in memory...")
    reglas_servicio_db['PESO_EQUIDAD_FINDES_MENSUAL'] = {"peso": 5000}
    
    ajustes_reglas = db_queries.cargar_ajustes_reglas_personal(fecha_inicio, fecha_fin)
    
    empleados = obtener_empleados(servicio_id, fecha_inicio, DIAS_DEL_BLOQUE)
    turnos_dict = obtener_turnos(servicio_id)
    
    historial_semana_previa = db_queries.cargar_guardias_previas(fecha_inicio, dias_atras=28, servicio_id=servicio_id)

    offset_dia = fecha_inicio_dt.weekday()
    
    modelo, turnos, flr_tracker, vars_turno_sem = construir_modelo(
        empleados, config_turnos, turnos_dict, demanda_req, ajustes_db,
        DIAS_DEL_BLOQUE, feriados_indices, offset_dia, num_semanas,
        reglas_servicio=reglas_servicio_db,
        ajustes_reglas_personal=ajustes_reglas,
        historial_semana_previa=historial_semana_previa,
        servicio_id=servicio_id
    )

    df_resultados, flrs_asignados, df_cat_semanas = resolver_modelo(
        modelo, turnos, flr_tracker, empleados, DIAS_DEL_BLOQUE, feriados_indices, 
        fecha_inicio, offset_dia, config_turnos, vars_turno_sem=vars_turno_sem,
        max_time_in_seconds=200
    )

    if df_resultados is not None:
        print("\n¡CRONOGRAMA GENERADO CON ÉXITO!")
        
        # Check Mansilla Diego's guardias
        print("\n[MANSILLA Diego's Guardias with Equity]")
        diego_guards = df_resultados[df_resultados['Personal'] == 'MANSILLA Diego'].sort_values('Fecha')
        for _, row in diego_guards.iterrows():
            dt = pd.to_datetime(row['Fecha'])
            is_f = (dt.weekday() >= 5) or (row['Fecha'] in ["2026-06-15", "2026-06-20"])
            print(f"  Fecha: {row['Fecha']} ({dt.strftime('%a')}), Turno: {row['Turno']}, EsFinde/Feriado: {is_f}")
            
        # Get weekend count for all monitoristas
        print("\n[Weekend/Holiday guardias per person in June with Equity]")
        finde_dates = ["2026-06-06", "2026-06-07", "2026-06-13", "2026-06-14", "2026-06-15", "2026-06-20", "2026-06-21", "2026-06-27", "2026-06-28"]
        df_finde = df_resultados[df_resultados['Fecha'].isin(finde_dates)]
        count_findes = df_finde.groupby('Personal').size().sort_values(ascending=False)
        for pers, cnt in count_findes.items():
            print(f"  {pers}: {cnt} shifts")
    else:
        print("ERROR: Infeasible or timeout with equity.")

if __name__ == "__main__":
    test_june_with_equity()
