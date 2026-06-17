import sqlite3

conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()

print("=== Puestos del Servicio 3 ===")
cursor.execute("SELECT id, nombre FROM puestos WHERE servicio_id = 3")
for r in cursor.fetchall():
    print(r)

print("\n=== Configuración de Turnos del Servicio 3 ===")
cursor.execute("SELECT id, nombre, hora_inicio, horas, orden, activo, dias_semana, puesto_id FROM turnos_config WHERE servicio_id = 3")
for r in cursor.fetchall():
    print(r)

print("\n=== Demanda Config de Turnos (Servicio 3) ===")
cursor.execute("""
    SELECT dc.id, p.nombre, dc.tipo_dia, dc.hora_inicio, dc.hora_fin, dc.cantidad_min, dc.cantidad_max, dc.dias_semana 
    FROM demanda_config dc
    JOIN puestos p ON dc.puesto_id = p.id
    WHERE p.servicio_id = 3
""")
for r in cursor.fetchall():
    print(r)

conn.close()
