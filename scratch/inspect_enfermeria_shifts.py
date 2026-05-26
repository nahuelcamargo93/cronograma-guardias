import sqlite3

conn = sqlite3.connect('cronograma_inteligente.db')
cur = conn.cursor()

# Get active shifts for service 2
cur.execute("SELECT nombre, hora_inicio, horas, dias_semana FROM turnos_config WHERE servicio_id = 2 AND activo = 1")
rows = cur.fetchall()
print("Enfermeria shifts:")
for row in rows:
    print(f"  {row[0]} (starts: {row[1]}, hours: {row[2]}, days: {row[3]})")

conn.close()
