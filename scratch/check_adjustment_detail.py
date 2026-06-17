import sqlite3
import json
import pandas as pd

conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()

print("=== AJUSTE REGLA SERVICIO 3 DETAIL ===")
cursor.execute("""
    SELECT codigo_regla, fecha_inicio, fecha_fin, accion, parametros_json
    FROM servicios_reglas_ajustes
    WHERE servicio_id = 3 AND activo = 1
""")
for code, fi, ff, act, params in cursor.fetchall():
    print(f"- Regla: {code} | Rango: {fi} a {ff} | Accion: {act}")
    print(f"  * Parámetros: {params}")

print("\n=== AJUSTES REGLAS PERSONAL SERVICIO 3 DETAIL ===")
cursor.execute("""
    SELECT s.personal_nombre, s.codigo_regla, s.fecha_inicio, s.fecha_fin, s.accion, s.parametros_json
    FROM personal_reglas_ajustes s
    JOIN personal p ON s.personal_nombre = p.nombre
    WHERE p.servicio_id = 3 AND s.activo = 1
    ORDER BY s.personal_nombre
""")
df_pa = pd.DataFrame(cursor.fetchall(), columns=['Nombre', 'Regla', 'Inicio', 'Fin', 'Accion', 'Params'])
pd.set_option('display.max_rows', 100)
print(df_pa)

conn.close()
