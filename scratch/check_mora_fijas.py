import database.connection as c
conn = c.get_connection()
rows = conn.execute("select id, personal_nombre, fecha, dia_semana, turno, activo from personal_asignaciones_fijas where personal_nombre='Mora, Sergio Enrique'").fetchall()
for r in rows:
    print(r)
