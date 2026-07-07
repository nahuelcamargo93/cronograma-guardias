import sqlite3
import os

db_path = "cronograma_inteligente.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

crono_id = 532

print("--- Guardias de GIMENEZ Adriana ---")
res = cursor.execute("SELECT fecha, turno, es_finde FROM guardias WHERE cronograma_id = ? AND nombre = 'GIMENEZ Adriana' ORDER BY fecha", (crono_id,)).fetchall()
for row in res:
    print(row)

conn.close()
