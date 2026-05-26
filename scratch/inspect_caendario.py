import sqlite3
import pandas as pd

conn = sqlite3.connect("cronograma_inteligente.db")
query = """
SELECT id, personal_nombre, codigo_regla, fecha_inicio, fecha_fin, accion, parametros_json, activo
FROM personal_reglas_ajustes
WHERE personal_nombre IN (
    'FERNANDEZ Celeste Ivana',
    'FERNANDEZ Claudia Elizabeth',
    'FERNANDEZ Juan Emir',
    'FLORES Enzo',
    'KOPRIVSEK Francisco',
    'OLGUIN ALDECO Jennifer Sofia',
    'ESCUDERO Gabriela'
)
ORDER BY personal_nombre, fecha_inicio, codigo_regla;
"""
df = pd.read_sql_query(query, conn)
print(df.to_string())
conn.close()
