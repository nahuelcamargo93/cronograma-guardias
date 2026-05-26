import sqlite3

conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()

print("\n--- Demanda Config para Servicio 2 ---")
# Demanda config connects to puesto, and puesto connects to servicio.
cursor.execute("""
    SELECT dc.id, p.nombre, dc.tipo_dia, dc.hora_inicio, dc.hora_fin, dc.cantidad_min, dc.cantidad_max 
    FROM demanda_config dc
    JOIN puestos p ON dc.puesto_id = p.id
    WHERE p.servicio_id = 2
""")
for r in cursor.fetchall():
    print(r)

conn.close()
