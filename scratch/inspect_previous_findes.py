import sqlite3
import pandas as pd

conn = sqlite3.connect('cronograma_inteligente.db')
pd.set_option('display.max_rows', None)

print("=== HISTORIAL DE FINES DE SEMANA TRABAJADOS - SERVICIO 1 ===")
# Obtener guardias de fines de semana del servicio 1 por persona y cronograma
df_g = pd.read_sql_query("""
    SELECT cronograma_id, nombre, COUNT(DISTINCT fecha) as dias_finde_trabajados
    FROM guardias
    WHERE servicio_id = 1 AND es_finde = 1
    GROUP BY cronograma_id, nombre
    ORDER BY cronograma_id, nombre
""", conn)
print(df_g)

# Ver cronogramas existentes
print("\n=== CRONOGRAMAS ===")
df_c = pd.read_sql_query("SELECT * FROM cronogramas", conn)
print(df_c)

conn.close()
