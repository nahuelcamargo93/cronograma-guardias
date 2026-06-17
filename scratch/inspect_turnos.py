import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import sqlite3
import pandas as pd

def inspect():
    conn = sqlite3.connect('cronograma_inteligente.db')
    cursor = conn.cursor()

    # Obtener todas las guardias del cronograma 357 para el servicio 2 en la semana del 6 al 12 de Julio de 2026
    df = pd.read_sql_query("""
        SELECT g.nombre, g.fecha, g.turno
        FROM guardias g
        JOIN personal p ON g.nombre = p.nombre
        WHERE g.cronograma_id = 357 
          AND p.servicio_id = 2 
          AND g.fecha BETWEEN '2026-07-06' AND '2026-07-12'
        ORDER BY g.nombre, g.fecha
    """, conn)

    # Agrupar por empleado y ver qué turnos hicieron esa semana
    print("Empleados del servicio 2, feriados previos y sus guardias en la semana del feriado (06-07 al 12-07):")
    
    # Cargar todos los feriados previos
    from database import queries as db_queries
    cursor.execute("SELECT nombre FROM personal WHERE servicio_id = 2 AND COALESCE(activo, 1) = 1")
    nombres_personal = [r[0] for r in cursor.fetchall()]
    df_personal = pd.DataFrame({'Nombre': nombres_personal})
    historial = db_queries.cargar_historial(df_personal, '2026-07-01')

    # Agrupar
    emp_groups = df.groupby('nombre')
    for nombre in sorted(nombres_personal):
        previos = historial.get(nombre, {}).get('Feriados_Previos', 0)
        licencias = db_queries.cargar_licencias_db('2026-07-01', '2026-07-31', servicio_id=2).get(nombre, [])
        lic_str = ", ".join([f"{l[0]}({l[1]} a {l[2]})" for l in licencias])
        
        ajustes_reglas = db_queries.cargar_ajustes_reglas_personal('2026-07-01', '2026-07-31').get(nombre, [])
        ajustes_str = ", ".join([f"{a['codigo_regla']}:{a['accion']}" for a in ajustes_reglas])

        if nombre in emp_groups.groups:
            g_emp = emp_groups.get_group(nombre)
            turnos_semana = [f"{row['fecha'][-2:]}:{row['turno']}" for _, row in g_emp.iterrows()]
            print(f"  {nombre:<22} (Previos: {previos}) -> {', '.join(turnos_semana)}")
        else:
            print(f"  {nombre:<22} (Previos: {previos}) -> SIN GUARDIAS (Licencias: {lic_str} | Ajustes: {ajustes_str})")

    conn.close()

if __name__ == '__main__':
    inspect()
