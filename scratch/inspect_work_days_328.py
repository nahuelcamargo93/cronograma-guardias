import sqlite3
import pandas as pd
from datetime import datetime, date

DB_PATH = "c:/Users/asus/Desktop/Ryoko/cronograma_inteligente/cronograma_inteligente.db"

def main():
    conn = sqlite3.connect(DB_PATH)
    
    # Cargar guardias
    guardias = pd.read_sql_query("""
        SELECT nombre, fecha, turno, horas 
        FROM guardias 
        WHERE cronograma_id = 328
    """, conn)
    
    # Calcular semana calendario para cada fecha
    guardias['fecha_dt'] = pd.to_datetime(guardias['fecha'])
    guardias['iso_week'] = guardias['fecha_dt'].apply(lambda x: x.isocalendar()[:2])
    
    # Agrupar por nombre y semana para contar los días distintos trabajados
    trabajo_por_semana = guardias.groupby(['nombre', 'iso_week'])['fecha'].nunique().reset_index(name='dias_trabajados')
    
    # Mostrar aquellos que trabajaron menos de 4 días en alguna semana
    bajo_trabajo = trabajo_por_semana[trabajo_por_semana['dias_trabajados'] < 4].sort_values(by=['nombre', 'iso_week'])
    
    print("=== Empleados con menos de 4 días de trabajo en semanas activas (Crono 328) ===")
    for _, row in bajo_trabajo.iterrows():
        # Ver qué turnos trabajaron en esa semana
        turnos_sem = guardias[(guardias['nombre'] == row['nombre']) & (guardias['iso_week'] == row['iso_week'])]
        turnos_str = ", ".join(f"{r['fecha']}({r['turno']})" for _, r in turnos_sem.iterrows())
        print(f"Empleado: {row['nombre']}, Semana: {row['iso_week']}, Días trabajados: {row['dias_trabajados']}, Detalles: {turnos_str}")
        
    conn.close()

if __name__ == '__main__':
    main()
