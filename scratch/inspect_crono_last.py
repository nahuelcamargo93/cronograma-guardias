import sqlite3
import pandas as pd

conn = sqlite3.connect('cronograma_inteligente.db')
pd.set_option('display.max_rows', None)

# Obtener guardias de fines de semana del servicio 1 por persona en el cronograma 305
print("=== GUARDIAS EN FINES DE SEMANA - CRONOGRAMA 305 ===")
df_305 = pd.read_sql_query("""
    SELECT nombre, fecha, turno, horas, es_finde
    FROM guardias
    WHERE servicio_id = 1 AND cronograma_id = 305 AND es_finde = 1
    ORDER BY nombre, fecha
""", conn)
print(df_305)

# Resumen de días de finde trabajados por persona en cronograma 305
print("\n=== RESUMEN DÍAS FINDE TRABAJADOS POR PERSONA - CRONOGRAMA 305 ===")
df_res_305 = pd.read_sql_query("""
    SELECT nombre, COUNT(*) as dias_finde_trabajados, SUM(horas) as horas_finde
    FROM guardias
    WHERE servicio_id = 1 AND cronograma_id = 305 AND es_finde = 1
    GROUP BY nombre
    ORDER BY dias_finde_trabajados DESC
""", conn)
print(df_res_305)

# Resumen de días de finde trabajados por persona en cronograma 307
print("\n=== RESUMEN DÍAS FINDE TRABAJADOS POR PERSONA - CRONOGRAMA 307 ===")
df_res_307 = pd.read_sql_query("""
    SELECT nombre, COUNT(*) as dias_finde_trabajados, SUM(horas) as horas_finde
    FROM guardias
    WHERE servicio_id = 1 AND cronograma_id = 307 AND es_finde = 1
    GROUP BY nombre
    ORDER BY dias_finde_trabajados DESC
""", conn)
print(df_res_307)

conn.close()
