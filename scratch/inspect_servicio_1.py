import sqlite3

conn = sqlite3.connect("cronograma_inteligente.db")
cursor = conn.cursor()

print("=== Puestos del Servicio 1 ===")
cursor.execute("SELECT id, nombre FROM puestos WHERE servicio_id = 1")
for row in cursor.fetchall():
    print(row)

print("\n=== Turnos configurados para el Servicio 1 ===")
cursor.execute("SELECT id, nombre, hora_inicio, horas, dias_semana, puesto_id, activo FROM turnos_config WHERE servicio_id = 1")
for row in cursor.fetchall():
    print(row)

print("\n=== Configuración de demanda para el Servicio 1 ===")
cursor.execute("""
    SELECT dc.id, p.nombre, dc.tipo_dia, dc.hora_inicio, dc.hora_fin, dc.cantidad_min, dc.cantidad_max, dc.dias_semana, dc.activo
    FROM demanda_config dc
    JOIN puestos p ON dc.puesto_id = p.id
    WHERE p.servicio_id = 1
""")
for row in cursor.fetchall():
    print(row)

print("\n=== Feriados ===")
cursor.execute("SELECT fecha, descripcion FROM feriados WHERE fecha LIKE '2026-07%'")
for row in cursor.fetchall():
    print(row)

print("\n=== Exclusiones de feriados para Servicio 1 ===")
cursor.execute("SELECT fecha FROM feriados_exclusiones WHERE servicio_id = 1")
for row in cursor.fetchall():
    print(row)

conn.close()
