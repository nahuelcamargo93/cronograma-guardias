import sqlite3
import pandas as pd
from datetime import datetime

conn = sqlite3.connect("cronograma_inteligente.db")
df = pd.read_sql_query("""
    SELECT DISTINCT fecha, es_finde 
    FROM guardias 
    WHERE cronograma_id = 1
    ORDER BY fecha
""", conn)
conn.close()

df['weekday'] = df['fecha'].apply(lambda x: datetime.strptime(x, "%Y-%m-%d").strftime("%A"))
print("=== WEEKENDS IN CRONOGRAMA 1 ===")
print(df[df['es_finde'] == 1].head(15))

print("\n=== NON-WEEKENDS IN CRONOGRAMA 1 WHERE ES_FINDE = 1 ===")
# Check if there are any non-Saturday/Sunday days with es_finde == 1
print(df[(df['es_finde'] == 1) & (~df['weekday'].isin(['Saturday', 'Sunday']))])
