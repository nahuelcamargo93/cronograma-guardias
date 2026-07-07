import database.connection as c
conn = c.get_connection()
rows = conn.execute("select id, personal_nombre, fecha_inicio, fecha_fin, activo from personal_reglas_ajustes where codigo_regla='ASIGNACION_FIJA' and activo=1").fetchall()
print("Active ASIGNACION_FIJA in personal_reglas_ajustes:")
for r in rows:
    print(r)
