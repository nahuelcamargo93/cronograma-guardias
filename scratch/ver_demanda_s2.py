import sqlite3

DB_PATH = "c:/Users/asus/Desktop/Ryoko/cronograma_inteligente/cronograma_inteligente.db"
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

print("=== Demanda Config Servicio 2 ===")
rows = cursor.execute("""
    SELECT dc.tipo_dia, p.nombre as puesto, dc.hora_inicio, dc.hora_fin, dc.cantidad_min, dc.cantidad_max, dc.dias_semana
    FROM demanda_config dc
    JOIN puestos p ON dc.puesto_id = p.id
    WHERE p.servicio_id = 2 AND dc.activo = 1
""").fetchall()

for r in rows:
    print(f"TipoDia: {r[0]}, Puesto: {r[1]}, Hora: {r[2]}-{r[3]}, Min: {r[4]}, Max: {r[5]}, Dias: {r[6]}")

conn.close()
