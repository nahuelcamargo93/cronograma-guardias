import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import sqlite3
from database import queries as db_queries
from database.data_loader import obtener_empleados

def inspect():
    conn = sqlite3.connect('cronograma_inteligente.db')
    cursor = conn.cursor()

    # 1. Obtener detalles del cronograma 357
    cursor.execute("SELECT id, fecha_inicio, fecha_fin FROM cronogramas WHERE id = 357")
    crono = cursor.fetchone()
    print("Cronograma:", crono)
    if not crono:
        return

    crono_id, fecha_inicio, fecha_fin = crono

    # 2. Feriados en la base de datos para este periodo
    feriados = db_queries.obtener_feriados(fecha_inicio, fecha_fin, servicio_id=2)
    print("Feriados en el periodo (servicio 2):", feriados)

    # 3. Cargar empleados del servicio 2 con sus datos previos al periodo
    import pandas as pd
    # Crear un df_personal ficticio con los nombres de enfermería
    cursor.execute("SELECT nombre FROM personal WHERE servicio_id = 2 AND COALESCE(activo, 1) = 1")
    nombres_personal = [r[0] for r in cursor.fetchall()]
    df_personal = pd.DataFrame({'Nombre': nombres_personal})
    
    # Cargar historial anterior a 2026-07-01
    historial = db_queries.cargar_historial(df_personal, fecha_inicio)

    print("\nFeriados Previos al 2026-07-01:")
    for nombre, hist in sorted(historial.items(), key=lambda x: x[1]['Feriados_Previos'], reverse=True):
        print(f"  {nombre}: {hist['Feriados_Previos']} feriados previos")

    # 4. Guardias asignadas en el cronograma 357 para los feriados de este periodo
    for f in feriados:
        cursor.execute("""
            SELECT g.nombre, g.turno
            FROM guardias g
            JOIN personal p ON g.nombre = p.nombre
            WHERE g.cronograma_id = ? AND g.fecha = ? AND p.servicio_id = 2
        """, (crono_id, f))
        guardias_f = cursor.fetchall()
        print(f"\nGuardias en feriado {f} del cronograma 357:")
        for g in guardias_f:
            previos = historial.get(g[0], {}).get('Feriados_Previos', 0)
            print(f"  {g[0]} (Previos: {previos}) en turno {g[1]}")

    conn.close()

if __name__ == '__main__':
    inspect()
