import database.connection as c
conn = c.get_connection()
rows = conn.execute("select id, fecha_inicio, fecha_fin, parametros_json, activo from personal_reglas_ajustes where personal_nombre='Mora, Sergio Enrique' and codigo_regla='ASIGNACION_FIJA'").fetchall()
for r in rows:
    print(r)
