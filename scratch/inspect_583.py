import sqlite3
import pandas as pd

conn = sqlite3.connect('cronograma_inteligente.db')

print("=== DETALLES CRONOGRAMA 583 ===")
df_crono = pd.read_sql_query("SELECT * FROM cronogramas WHERE id = 583", conn)
print(df_crono)

print("\n=== GUARDIAS DEL CRONOGRAMA 583 (primeras 20) ===")
df_guardias = pd.read_sql_query("SELECT nombre, fecha, turno, horas, es_finde FROM guardias WHERE cronograma_id = 583 ORDER BY fecha, turno LIMIT 20", conn)
print(df_guardias)

print("\n=== TOTAL DE GUARDIAS DEL CRONOGRAMA 583 ===")
count = pd.read_sql_query("SELECT COUNT(*) as total FROM guardias WHERE cronograma_id = 583", conn)
print(count)

print("\n=== RANGO DE FECHAS EN LAS GUARDIAS DE 583 ===")
fechas = pd.read_sql_query("SELECT MIN(fecha) as min_f, MAX(fecha) as max_f FROM guardias WHERE cronograma_id = 583", conn)
print(fechas)

print("\n=== EMPLEADOS EN LAS GUARDIAS DE 583 ===")
emps = pd.read_sql_query("SELECT DISTINCT nombre FROM guardias WHERE cronograma_id = 583", conn)
print(emps)

conn.close()
