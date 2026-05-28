import sqlite3
conn = sqlite3.connect('cronograma_inteligente.db')
cur = conn.cursor()

cur.execute("""
    SELECT id, personal_nombre, codigo_regla, fecha_inicio, fecha_fin, accion, activo 
    FROM personal_reglas_ajustes 
    WHERE codigo_regla IN ('MIN_FINDES_MES', 'EXACTO_FINDES_MES') 
    ORDER BY personal_nombre
""")
print('=== Suspensiones de MIN/EXACTO FINDES ===')
for r in cur.fetchall():
    print(r)

cur.execute("""
    SELECT id, codigo_regla, fecha_inicio, fecha_fin, accion, activo 
    FROM personal_reglas_ajustes 
    WHERE personal_nombre LIKE '%Zeballos%'
""")
print('\n=== Ajustes de Zeballos ===')
for r in cur.fetchall():
    print(r)

conn.close()
