import pandas as pd
from datetime import datetime, date
from database.connection import get_connection
from database import queries as db_queries
from reportes.servicio_2_enfermeria.enfermeria import generar_y_exportar

def main():
    # Inicializar Base de Datos y licencias
    db_queries.init_licencias(servicio_id=2)
    
    with get_connection() as conn:
        # 1. Buscar el último cronograma de enfermería (servicio_id = 2)
        row_crono = conn.execute("""
            SELECT DISTINCT c.id, c.fecha_inicio, c.fecha_fin, c.notas
            FROM cronogramas c
            JOIN guardias g ON c.id = g.cronograma_id
            JOIN personal p ON g.nombre = p.nombre
            WHERE p.servicio_id = 2
            ORDER BY c.id DESC
            LIMIT 1
        """).fetchone()
        
        if not row_crono:
            print("No se encontró ningún cronograma para el Servicio 2 (Enfermería) en la base de datos.")
            return
            
        crono_id, fecha_inicio, fecha_fin, notas = row_crono
        print(f"Exportando Cronograma ID: {crono_id} ({fecha_inicio} -> {fecha_fin})")
        
        # 2. Cargar guardias del cronograma
        rows_guardias = conn.execute("""
            SELECT fecha, turno, nombre
            FROM guardias
            WHERE cronograma_id = ?
        """, (crono_id,)).fetchall()
        df_resultados = pd.DataFrame(rows_guardias, columns=['Fecha', 'Turno', 'Personal'])
        df_resultados['Kinesiologo'] = df_resultados['Personal']
        
        # 3. Cargar personal
        rows_personal = conn.execute("""
            SELECT nombre, categoria, rol
            FROM personal
            WHERE servicio_id = 2 AND COALESCE(activo, 1) = 1
        """,).fetchall()
        df_personal = pd.DataFrame(rows_personal, columns=['Nombre', 'Categoria', 'Rol'])
        
        # 4. Cargar FLRs asignados
        rows_flrs = conn.execute("""
            SELECT nombre, fecha_inicio, fecha_fin
            FROM flr_asignados
            WHERE cronograma_id = ?
        """, (crono_id,)).fetchall()
        flrs_asignados = [{'nombre': r[0], 'fecha_inicio': r[1], 'fecha_fin': r[2]} for r in rows_flrs]
        
        # 5. Cargar categorías semanales
        rows_cats = conn.execute("""
            SELECT nombre, fecha_lunes, categoria
            FROM semanas_categorias
            WHERE cronograma_id = ?
        """, (crono_id,)).fetchall()
        df_cat_semanas = pd.DataFrame(rows_cats, columns=['Nombre', 'Fecha_Lunes', 'Categoria'])
        
        # 6. Datos de tiempo
        dt_inicio = date.fromisoformat(fecha_inicio)
        dt_fin = date.fromisoformat(fecha_fin)
        dias_del_bloque = (dt_fin - dt_inicio).days + 1
        offset_dia = dt_inicio.weekday()
        
        # Feriados
        feriados_db = db_queries.obtener_feriados(fecha_inicio, fecha_fin, servicio_id=2)
        feriados_indices = []
        for f_str in feriados_db:
            f_dt = date.fromisoformat(f_str)
            delta = (f_dt - dt_inicio).days
            if 0 <= delta < dias_del_bloque:
                feriados_indices.append(delta)
                
    # Generar y exportar reporte
    file_name = f"Cronograma_Enfermeria_UTI_Crono_{crono_id}.xlsx"
    generar_y_exportar(
        df_resultados, df_personal, dias_del_bloque, feriados_indices,
        fecha_inicio, offset_dia, config_turnos={}, num_semanas=4,
        flrs_asignados=flrs_asignados, df_cat_semanas=df_cat_semanas,
        file_name=file_name, crono_id=crono_id
    )
    print(f"Reporte exportado con éxito a: {file_name}")

if __name__ == "__main__":
    main()
