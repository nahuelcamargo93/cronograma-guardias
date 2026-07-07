import sqlite3
import pandas as pd
import datetime
import os
import sys

# Add project root to sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from database import queries as db_queries
from database.data_loader import obtener_empleados
from reportes.servicio_2_enfermeria.enfermeria import generar_y_exportar as gen_enf

def main():
    conn = sqlite3.connect('cronograma_inteligente.db')
    cursor = conn.cursor()

    crono_id = 543
    crono = cursor.execute("""
        SELECT id, fecha_inicio, fecha_fin
        FROM cronogramas
        WHERE id = ?
    """, (crono_id,)).fetchone()
    
    if not crono:
        print(f"ERROR: No se encontró el Cronograma ID {crono_id} en la base de datos.")
        conn.close()
        return

    servicio_id = 2
    crono_id, fecha_inicio, fecha_fin = crono
    print(f"[OK] Exportando Cronograma ID {crono_id} para Servicio {servicio_id}")
    print(f"     Período: {fecha_inicio} al {fecha_fin}")

    # 1. Cargar df_resultados
    df_resultados = pd.read_sql_query("""
        SELECT fecha as Fecha, nombre as Personal, turno as Turno
        FROM guardias
        WHERE cronograma_id = ?
    """, conn, params=(crono_id,))

    # Agregar Dia_Semana
    dias_nombres = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    df_resultados['Dia_Semana'] = df_resultados['Fecha'].apply(
        lambda f: dias_nombres[datetime.datetime.strptime(f, "%Y-%m-%d").weekday()]
    )

    # Calcular variables de fecha
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

    # 2. Cargar df_personal y turnos
    config_turnos, _, _, _ = db_queries.cargar_configuracion_turnos(
        servicio_id=servicio_id, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin
    )
    db_queries.init_licencias(servicio_id)
    empleados = obtener_empleados(servicio_id, fecha_inicio, total_dias)
    offset_dia = fecha_inicio_dt.weekday()

    df_personal = pd.DataFrame([vars(e) for e in empleados])
    df_personal = df_personal.rename(columns={'nombre': 'Nombre', 'rol': 'Rol'})

    # 3. Cargar semanas_categorias (df_cat_semanas)
    df_cat_semanas = pd.read_sql_query("""
        SELECT nombre as Nombre, fecha_lunes as Fecha_Lunes, categoria as Categoria
        FROM semanas_categorias
        WHERE cronograma_id = ?
    """, conn, params=(crono_id,))

    # 4. Cargar flr_asignados
    cursor.execute("""
        SELECT nombre, fecha_inicio, fecha_fin
        FROM flr_asignados
        WHERE cronograma_id = ?
    """, (crono_id,))
    flrs_rows = cursor.fetchall()
    flrs_asignados = [{'nombre': r[0], 'fecha_inicio': r[1], 'fecha_fin': r[2]} for r in flrs_rows]

    conn.close()

    # 5. Exportar al Excel de prueba
    output_file = 'scratch/Cronograma_Enfermeria_UTI_Julio26_Test.xlsx'
    print(f"Exportando a {output_file}...")
    gen_enf(df_resultados, df_personal, total_dias, feriados_indices, fecha_inicio, offset_dia, config_turnos, num_semanas, flrs_asignados, df_cat_semanas, file_name=output_file, crono_id=crono_id)
    print(f"[SUCCESS] Archivo generado en: {output_file}")

if __name__ == '__main__':
    main()
