import sqlite3
import json

conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()

print("DEMANDA CONFIG:")
cursor.execute("""
    SELECT dc.id, p.nombre, dc.tipo_dia, dc.hora_inicio, dc.hora_fin, dc.cantidad_min, dc.cantidad_max 
    FROM demanda_config dc
    JOIN puestos p ON dc.puesto_id = p.id
    WHERE p.servicio_id = 2
""")
for row in cursor.fetchall():
    print(row)

print("\nSERVICIOS:")
cursor.execute("SELECT id, nombre FROM servicios")
print(cursor.fetchall())

print("\nREGLAS DE SERVICIO 2:")
cursor.execute("""
    SELECT rc.codigo_regla, sr.parametros_json 
    FROM servicios_reglas sr
    JOIN reglas_catalogo rc ON sr.regla_id = rc.id
    WHERE sr.servicio_id = 2
""")
for row in cursor.fetchall():
    print(row)

conn.close()
