import sqlite3

conn = sqlite3.connect('cronograma_inteligente.db')
cur = conn.cursor()

print("=== REGISTROS EN demanda_config PARA servicio_id = 2 ===")
rows = cur.execute("""
    SELECT dc.id, p.nombre as puesto, dc.puesto_id, dc.tipo_dia, dc.hora_inicio, dc.hora_fin, dc.cantidad_min, dc.cantidad_max
    FROM demanda_config dc
    JOIN puestos p ON dc.puesto_id = p.id
    WHERE p.servicio_id = 2
""").fetchall()

for r in rows:
    print(f"ID: {r[0]} | Puesto: {r[1]} (puesto_id: {r[2]}) | Tipo: {r[3]} | Horario: {r[4]}-{r[5]} | Min: {r[6]} | Max: {r[7]}")

conn.close()
