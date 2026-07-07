import database.connection as c
conn = c.get_connection()
rows = conn.execute("select id, personal_nombre, codigo_regla, parametros_json, activo from personal_reglas where personal_nombre='Mora, Sergio Enrique'").fetchall()
for r in rows:
    print(r)
