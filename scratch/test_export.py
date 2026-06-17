import sqlite3
import pandas as pd
import datetime
from database import queries as db_queries
from database.data_loader import obtener_empleados

def main():
    conn = sqlite3.connect('cronograma_inteligente.db')
    cursor = conn.cursor()
    
    servicio_id = 1
    crono = cursor.execute("""
        SELECT c.id, c.fecha_inicio, c.fecha_fin
        FROM cronogramas c
        JOIN guardias g ON c.id = g.cronograma_id
        JOIN personal p ON g.nombre = p.nombre
        WHERE p.servicio_id = ?
        ORDER BY c.id DESC
        LIMIT 1
    """, (servicio_id,)).fetchone()

    if not crono:
        print("ERROR: No se encontró ningún cronograma.")
        conn.close()
        return

    crono_id, fecha_inicio, fecha_fin = crono
    print(f"[TEST] Exportando Cronograma ID {crono_id} para Servicio {servicio_id}")
    
    df_resultados = pd.read_sql_query("""
        SELECT fecha as Fecha, nombre as Personal, turno as Turno
        FROM guardias
        WHERE cronograma_id = ?
    """, conn, params=(crono_id,))

    dias_nombres = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    df_resultados['Dia_Semana'] = df_resultados['Fecha'].apply(
        lambda f: dias_nombres[datetime.datetime.strptime(f, "%Y-%m-%d").weekday()]
    )

    fecha_inicio_dt = datetime.datetime.strptime(fecha_inicio, "%Y-%m-%d")
    fecha_fin_dt = datetime.datetime.strptime(fecha_fin, "%Y-%m-%d")
    total_dias = (fecha_fin_dt - fecha_inicio_dt).days + 1
    num_semanas = (total_dias + 6) // 7

    feriados_db = db_queries.obtener_feriados(fecha_inicio, fecha_fin, servicio_id=servicio_id)
    feriados_indices = []
    for f_str in feriados_db:
        f_dt = datetime.datetime.strptime(f_str, "%Y-%m-%d")
        delta = (f_dt - fecha_inicio_dt).days
        if 0 <= delta < total_dias:
            feriados_indices.append(delta)

    config_turnos, _, _, _ = db_queries.cargar_configuracion_turnos(
        servicio_id=servicio_id, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin
    )
    db_queries.init_licencias(servicio_id)
    empleados = obtener_empleados(servicio_id, fecha_inicio, total_dias)
    offset_dia = fecha_inicio_dt.weekday()

    df_personal = pd.DataFrame([vars(e) for e in empleados])
    df_personal = df_personal.rename(columns={'nombre': 'Nombre', 'rol': 'Rol'})

    conn.close()

    test_file_name = 'Cronograma_Servicio_Kinesiologia_Julio26_TEST.xlsx'
    
    from reportes.servicio_1_kinesiologia.kinesiologia import generar_y_exportar as gen_kin
    gen_kin(
        df_resultados, df_personal, total_dias, feriados_indices, 
        fecha_inicio, offset_dia, config_turnos, num_semanas, 
        file_name=test_file_name, crono_id=crono_id
    )
    print(f"[TEST] Reporte exportado a {test_file_name} correctamente.")

if __name__ == '__main__':
    main()
