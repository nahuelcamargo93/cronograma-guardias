import database.connection as c
conn = c.get_connection()
rows = conn.execute("""
    SELECT fecha, turno, horas 
    FROM guardias 
    WHERE nombre = 'Mora, Sergio Enrique' 
      AND cronograma_id = 549
    ORDER BY fecha
""").fetchall()
print("Mora's assignments in cronograma 549:")
for r in rows:
    print(r)
