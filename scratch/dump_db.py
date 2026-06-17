import sqlite3
import json

db_path = "cronograma_inteligente.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("--- SERVICIOS ---")
cursor.execute("SELECT id, nombre FROM servicios")
for row in cursor.fetchall():
    print(row)

print("\n--- REGLAS ACTIVAS PARA SERVICIO 2 ---")
cursor.execute("SELECT id, codigo_regla, parametros_json, activo FROM servicios_reglas WHERE servicio_id = 2")
for row in cursor.fetchall():
    print(row)

print("\n--- PUESTOS PARA SERVICIO 2 ---")
cursor.execute("SELECT id, nombre, servicio_id FROM puestos WHERE servicio_id = 2")
for row in cursor.fetchall():
    print(row)

print("\n--- TURNOS PARA SERVICIO 2 ---")
cursor.execute("SELECT id, nombre, hora_inicio, horas, servicio_id FROM turnos_config WHERE servicio_id = 2")
for row in cursor.fetchall():
    print(row)

print("\n--- DEMANDA CONFIGURADA PARA SERVICIO 2 ---")
cursor.execute("""
    SELECT dc.id, p.nombre, dc.tipo_dia, dc.hora_inicio, dc.hora_fin, dc.cantidad_min, dc.cantidad_max 
    FROM demanda_config dc
    JOIN puestos p ON dc.puesto_id = p.id
    WHERE p.servicio_id = 2
""")
for row in cursor.fetchall():
    print(row)

conn.close()
