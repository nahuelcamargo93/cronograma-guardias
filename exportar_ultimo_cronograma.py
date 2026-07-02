import sqlite3
import pandas as pd
import sys
import datetime
from database import queries as db_queries
from database.data_loader import obtener_empleados
# VARIABLE CONFIGURABLE DE ID DE CRONOGRAMA
# Dejar en None para exportar el último cronograma de forma automática o elegir por consola.
# Cambiar por un número entero (ej: 191) para forzar la exportación de un cronograma específico.
CRONOGRAMA_ID_FORZADO = 591

def main():
    conn = sqlite3.connect('cronograma_inteligente.db')
    cursor = conn.cursor()

    if CRONOGRAMA_ID_FORZADO is not None:
        crono_id = CRONOGRAMA_ID_FORZADO
        crono = cursor.execute("""
            SELECT id, fecha_inicio, fecha_fin
            FROM cronogramas
            WHERE id = ?
        """, (crono_id,)).fetchone()
        
        if not crono:
            print(f"ERROR: No se encontró el Cronograma ID {crono_id} en la base de datos.")
            conn.close()
            return
            
        servicio_row = cursor.execute("""
            SELECT DISTINCT p.servicio_id
            FROM guardias g
            JOIN personal p ON g.nombre = p.nombre
            WHERE g.cronograma_id = ?
            LIMIT 1
        """, (crono_id,)).fetchone()
        
        if servicio_row:
            servicio_id = servicio_row[0]
        else:
            print(f"ERROR: No se pudo determinar el servicio para el Cronograma ID {crono_id} (no tiene guardias asignadas).")
            conn.close()
            return
    else:
        if len(sys.argv) > 1:
            try:
                servicio_id = int(sys.argv[1])
            except ValueError:
                print("ERROR: El ID del servicio debe ser un número entero.")
                conn.close()
                return
        else:
            print("=== EXPORTADOR DE ÚLTIMO CRONOGRAMA ===")
            print("Servicios:")
            print("  1: Kinesiología Crítica")
            print("  2: Enfermería UTI")
            print("  3: Área Médica UTI")
            print("  4: Personal de Monitoreo (COM)")
            try:
                val = input("Ingrese el ID del servicio (1-4): ")
                servicio_id = int(val)
            except (ValueError, KeyboardInterrupt):
                print("\nOperación cancelada.")
                conn.close()
                return

        if servicio_id not in [1, 2, 3, 4]:
            print(f"ERROR: ID de servicio {servicio_id} no válido. Debe ser 1, 2, 3 o 4.")
            conn.close()
            return

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
            print(f"ERROR: No se encontró ningún cronograma para el Servicio {servicio_id} en la base de datos.")
            conn.close()
            return

    crono_id, fecha_inicio, fecha_fin = crono
    print(f"\n[OK] Encontrado Cronograma ID {crono_id} para Servicio {servicio_id}")
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
    # Cargar licencias en memoria (LAR, LPP, LM, CM) — necesario para los reportes
    db_queries.init_licencias(servicio_id)
    empleados = obtener_empleados(servicio_id, fecha_inicio, total_dias)
    offset_dia = fecha_inicio_dt.weekday()

    df_personal = pd.DataFrame([vars(e) for e in empleados])
    df_personal = df_personal.rename(columns={'nombre': 'Nombre', 'rol': 'Rol'})

    # 3. Cargar semanas_categorias (df_cat_semanas) si el servicio lo usa (servicio 2 y 3)
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

    # 5. Exportar al Excel correspondiente
    try:
        if servicio_id == 1:
            from reportes.servicio_1_kinesiologia.kinesiologia import generar_y_exportar as gen_kin
            gen_kin(df_resultados, df_personal, total_dias, feriados_indices, fecha_inicio, offset_dia, config_turnos, num_semanas, crono_id=crono_id)
        elif servicio_id == 2:
            from reportes.servicio_2_enfermeria.enfermeria import generar_y_exportar as gen_enf
            gen_enf(df_resultados, df_personal, total_dias, feriados_indices, fecha_inicio, offset_dia, config_turnos, num_semanas, flrs_asignados, df_cat_semanas, crono_id=crono_id)
        elif servicio_id == 3:
            from reportes.servicio_3_medicos.medicos import generar_y_exportar as gen_med
            gen_med(df_resultados, df_personal, total_dias, feriados_indices, fecha_inicio, offset_dia, config_turnos, num_semanas, flrs_asignados, df_cat_semanas, crono_id=crono_id)
        elif servicio_id == 4:
            from reportes.servicio_4_monitoreo.com import generar_y_exportar as gen_com
            gen_com(df_resultados, df_personal, total_dias, feriados_indices, fecha_inicio, offset_dia, config_turnos, num_semanas, crono_id=crono_id)
            
        print(f"\n[SUCCESS] Reporte Excel generado con éxito para Servicio {servicio_id}!")
    except PermissionError:
        print("\n[ERROR] No se pudo escribir el archivo Excel. Asegúrate de cerrar la planilla correspondiente y vuelve a intentarlo.")
    except Exception as e:
        print(f"\n[ERROR] Error inesperado al exportar el reporte: {e}")

if __name__ == '__main__':
    main()
