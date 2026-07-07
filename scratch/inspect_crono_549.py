import database.connection as c
conn = c.get_connection()
crono = conn.execute("select * from cronogramas where id = 549").fetchone()
print("Cronograma:", crono)
guardias = conn.execute("select nombre, fecha, turno, horas from guardias where cronograma_id = 549 and nombre = 'Mora, Sergio Enrique'").fetchall()
print("Guardias Mora en 549:")
for g in guardias:
    print(g)
