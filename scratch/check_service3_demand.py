import sqlite3
import json

conn = sqlite3.connect('cronograma_inteligente.db')
cur = conn.cursor()

# Get service name
cur.execute("SELECT nombre FROM servicios WHERE id = 3")
print("Servicio:", cur.fetchone()[0])

# Get number of active doctors
cur.execute("SELECT COUNT(*) FROM personal WHERE servicio_id = 3 AND activo = 1")
print("Total active doctors:", cur.fetchone()[0])

# Get puestos for service 3
cur.execute("SELECT id, nombre FROM puestos WHERE servicio_id = 3")
puestos = cur.fetchall()
print("Puestos:", puestos)

# Get turnos config
cur.execute("SELECT nombre, hora_inicio, horas, dias_semana FROM turnos_config WHERE servicio_id = 3")
print("\nTurnos Config:")
for row in cur.fetchall():
    print("  ", row)

# Get demand configs
print("\nDemand Configs:")
for p_id, p_name in puestos:
    cur.execute("""
        SELECT tipo_dia, hora_inicio, hora_fin, cantidad_min, cantidad_max, dias_semana 
        FROM demanda_config 
        WHERE puesto_id = ?
    """, (p_id,))
    print(f"  Puesto {p_name}:")
    for row in cur.fetchall():
        print("    ", row)

conn.close()
