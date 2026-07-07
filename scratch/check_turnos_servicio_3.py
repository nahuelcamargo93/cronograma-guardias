import sqlite3
import json

conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()

print("=== TURNOS CONFIG (servicio_id = 3) ===")
cursor.execute("SELECT * FROM turnos_config WHERE servicio_id = 3")
for r in cursor.fetchall():
    print(r)

print("\n=== TURNOS AJUSTES ===")
cursor.execute("SELECT * FROM turnos_ajustes")
for r in cursor.fetchall():
    print(r)

print("\n=== SERVICIOS REGLAS (servicio_id = 3) ===")
cursor.execute("SELECT codigo_regla, parametros_json, activo FROM servicios_reglas WHERE servicio_id = 3")
for r in cursor.fetchall():
    print(r)

print("\n=== SERVICIOS REGLAS (servicio_id = 3) ===")
cursor.execute("SELECT codigo_regla, parametros_json FROM servicios_reglas WHERE servicio_id = 3 AND codigo_regla IN ('DESCANSO_ENTRE_TURNOS', 'PENALIZACION_TURNO')")
for r in cursor.fetchall():
    print(r)

conn.close()
