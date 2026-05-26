import sqlite3
import pandas as pd
from datetime import datetime, date
import database.queries as db_queries
from reportes.kinesiologia import generar_y_exportar as gen_kin
from reportes.enfermeria import generar_y_exportar as gen_enf
from reportes.medicos import generar_y_exportar as gen_med
from reportes.com import generar_y_exportar as gen_com

def main():
    conn = sqlite3.connect('cronograma_inteligente.db')
    conn.row_factory = sqlite3.Row
    
    # Inicializar licencias
    db_queries.init_licencias()
    
    # 1. Obtener la lista de servicios
    servicios = conn.execute("SELECT id, nombre FROM servicios").fetchall()
    print("=== Servicios detectados ===")
    for s in servicios:
        print(f"ID: {s['id']}, Nombre: {s['nombre']}")
    print("-" * 50)
    
    for s in servicios:
        servicio_id = s['id']
        servicio_nombre = s['nombre']
        
        # Encontrar el último cronograma para este servicio
        cron_row = conn.execute("""
            SELECT DISTINCT c.id, c.fecha_inicio, c.fecha_fin
            FROM cronogramas c
            JOIN guardias g ON g.cronograma_id = c.id
            JOIN personal p ON g.nombre = p.nombre
            WHERE p.servicio_id = ?
            ORDER BY c.fecha_inicio DESC, c.id DESC
            LIMIT 1
        """, (servicio_id,)).fetchone()
        
        if not cron_row:
            print(f"No hay cronogramas para el servicio {servicio_nombre} (ID: {servicio_id})")
            continue
            
        cronograma_id = cron_row['id']
        fecha_inicio = cron_row['fecha_inicio']
        fecha_fin = cron_row['fecha_fin']
        print(f"Procesando servicio: {servicio_nombre} (ID: {servicio_id}) - Cronograma {cronograma_id}: {fecha_inicio} a {fecha_fin}")
        
        # Obtener guardias
        guardias_rows = conn.execute("""
            SELECT g.fecha as Fecha, g.turno as Turno, g.nombre as Personal
            FROM guardias g
            WHERE g.cronograma_id = ?
        """, (cronograma_id,)).fetchall()
        
        df_resultados = pd.DataFrame([dict(r) for r in guardias_rows])
        if df_resultados.empty:
            print("  [ERROR] No se encontraron guardias!")
            continue
            
        dias_nombres = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        df_resultados['Dia_Semana'] = df_resultados['Fecha'].apply(lambda x: dias_nombres[datetime.strptime(x, "%Y-%m-%d").weekday()])
        df_resultados['Kinesiologo'] = df_resultados['Personal']
        
        # Obtener personal del servicio
        personal_rows = conn.execute("""
            SELECT nombre as Nombre, rol as Rol, categoria as Categoria
            FROM personal
            WHERE servicio_id = ?
        """, (servicio_id,)).fetchall()
        df_personal = pd.DataFrame([dict(r) for r in personal_rows])
        df_personal = db_queries.cargar_datos_personales_bd(df_personal)
        
        # Cargar historial para que los acumulados previos no sean 0
        historial = db_queries.cargar_historial(df_personal, fecha_inicio)
        df_personal['horas_anuales_previas'] = df_personal['Nombre'].map(lambda n: historial.get(n, {}).get('Horas_Anuales_Previas', 0))
        df_personal['findes_semanas_previos'] = df_personal['Nombre'].map(lambda n: historial.get(n, {}).get('Findes_Semanas_Previos', 0))
        df_personal['findes_largos_3_previos'] = df_personal['Nombre'].map(lambda n: historial.get(n, {}).get('Findes_Largos_3_Previos', 0))
        df_personal['findes_largos_4_previos'] = df_personal['Nombre'].map(lambda n: historial.get(n, {}).get('Findes_Largos_4_Previos', 0))
        df_personal['fecha_inicio_historial'] = df_personal['Nombre'].map(lambda n: historial.get(n, {}).get('Fecha_Inicio_Historial'))
        
        # Obtener FLRs asignados
        flrs_rows = conn.execute("""
            SELECT nombre, fecha_inicio, fecha_fin
            FROM flr_asignados
            WHERE cronograma_id = ?
        """, (cronograma_id,)).fetchall()
        flrs_asignados = [dict(r) for r in flrs_rows]
        
        # Obtener semanas_categorias
        cat_rows = conn.execute("""
            SELECT nombre as Nombre, fecha_lunes as Fecha_Lunes, categoria as Categoria
            FROM semanas_categorias
            WHERE cronograma_id = ?
        """, (cronograma_id,)).fetchall()
        df_cat_semanas = pd.DataFrame([dict(r) for r in cat_rows])
        
        # Cargar configuración de turnos
        config_turnos, metadata_turnos_raw, demanda_req, ajustes_db = db_queries.cargar_configuracion_turnos(
            servicio_id=servicio_id, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin
        )
        
        fecha_inicio_dt = datetime.strptime(fecha_inicio, "%Y-%m-%d")
        fecha_fin_dt = datetime.strptime(fecha_fin, "%Y-%m-%d")
        total_dias = (fecha_fin_dt - fecha_inicio_dt).days + 1
        num_semanas = (total_dias + 6) // 7
        offset_dia = fecha_inicio_dt.weekday()
        
        from data import FERIADOS
        feriados_indices = []
        for f_str in FERIADOS:
            f_dt = datetime.strptime(f_str, "%Y-%m-%d")
            delta = (f_dt - fecha_inicio_dt).days
            if 0 <= delta < total_dias:
                feriados_indices.append(delta)
                
        try:
            if servicio_id == 1:
                gen_kin(df_resultados, df_personal, total_dias, feriados_indices, fecha_inicio, offset_dia, config_turnos, num_semanas)
            elif servicio_id == 2:
                gen_enf(df_resultados, df_personal, total_dias, feriados_indices, fecha_inicio, offset_dia, config_turnos, num_semanas, flrs_asignados, df_cat_semanas, file_name='Cronograma_Enfermeria_UTI_actualizado.xlsx')
            elif servicio_id == 3:
                gen_med(df_resultados, df_personal, total_dias, feriados_indices, fecha_inicio, offset_dia, config_turnos, num_semanas, flrs_asignados, df_cat_semanas)
            elif servicio_id == 4:
                gen_com(df_resultados, df_personal, total_dias, feriados_indices, fecha_inicio, offset_dia, config_turnos, num_semanas)
            print(f"  [OK] Excel generado con éxito para {servicio_nombre}")
        except Exception as e:
            print(f"  [ERROR] Error al generar Excel para {servicio_nombre}: {e}")
            import traceback
            traceback.print_exc()
        print("-" * 50)
        
    conn.close()

if __name__ == '__main__':
    main()
