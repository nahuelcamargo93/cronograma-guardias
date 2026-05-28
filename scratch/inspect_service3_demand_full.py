import sqlite3

conn = sqlite3.connect("cronograma_inteligente.db")
cursor = conn.cursor()

print("=== DEMANDA CONFIG FOR SERVICE 3 (FULL) ===")
cursor.execute("""
    SELECT dc.id, p.nombre, dc.tipo_dia, dc.hora_inicio, dc.hora_fin, dc.cantidad_min, dc.cantidad_max, dc.dias_semana
    FROM demanda_config dc
    JOIN puestos p ON dc.puesto_id = p.id
    WHERE p.servicio_id = 3
""")
for row in cursor.fetchall():
    print(f"ID: {row[0]} | Puesto: {row[1]} | Tipo: {row[2]} | Horario: {row[3]}-{row[4]} | Cantidad: {row[5]}-{row[6]} | Dias: {row[7]}")

print("\n=== DEMANDA AJUSTES FOR SERVICE 3 (FULL) ===")
cursor.execute("""
    SELECT da.id, p.nombre, da.fecha_inicio, da.fecha_fin, da.cantidad_min, da.cantidad_max
    FROM demanda_ajustes da
    JOIN demanda_config dc ON da.demanda_config_id = dc.id
    JOIN puestos p ON dc.puesto_id = p.id
    WHERE p.servicio_id = 3
""")
for row in cursor.fetchall():
    print(f"ID: {row[0]} | Puesto: {row[1]} | Rango: {row[2]} a {row[3]} | Cantidad: {row[4]}-{row[5]}")

conn.close()
