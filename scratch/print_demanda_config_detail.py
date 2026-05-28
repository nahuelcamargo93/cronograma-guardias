import sqlite3

conn = sqlite3.connect("cronograma_inteligente.db")
cursor = conn.cursor()
cursor.execute("SELECT * FROM demanda_config LIMIT 1")
col_names = [description[0] for description in cursor.description]
print("Columns in demanda_config:", col_names)

cursor.execute("""
    SELECT dc.*, p.nombre as puesto_nombre
    FROM demanda_config dc
    JOIN puestos p ON dc.puesto_id = p.id
    WHERE p.servicio_id = 3
""")
rows = cursor.fetchall()
for r in rows:
    row_dict = dict(zip(col_names + ["puesto_nombre"], r))
    print(row_dict)
conn.close()
