import sqlite3
import pandas as pd

conn = sqlite3.connect('cronograma_inteligente.db')

# Cargar demanda base para Finde_Feriado
df_dem = pd.read_sql_query("""
    SELECT dc.id, p.nombre as puesto, dc.cantidad_min, dc.cantidad_max, dc.hora_inicio, dc.hora_fin
    FROM demanda_config dc
    JOIN puestos p ON dc.puesto_id = p.id
    WHERE p.servicio_id = 2 AND dc.activo = 1 AND dc.tipo_dia = 'Finde_Feriado'
""", conn)
print("=== DEMANDA DE FIN DE SEMANA (SERVIZIO 2) ===")
print(df_dem)

total_min_dia = df_dem['cantidad_min'].sum()
total_max_dia = df_dem['cantidad_max'].sum()
print(f"\nTotal vacantes MIN por día de fin de semana: {total_min_dia}")
print(f"Total vacantes MAX por día de fin de semana: {total_max_dia}")

conn.close()
