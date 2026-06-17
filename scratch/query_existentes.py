import sqlite3

DB_PATH = "cronograma_inteligente.db"
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

print("--- CRONOGRAMAS Y SUS GUARDIAS DE SERVICIO 3 ---")
cursor.execute("""
    SELECT DISTINCT c.id, c.fecha_inicio, c.fecha_fin, c.estado, c.notas
    FROM cronogramas c
    JOIN guardias g ON c.id = g.cronograma_id
    WHERE g.servicio_id = 3;
""")
cronos = cursor.fetchall()
print(f"Encontrados {len(cronos)} cronogramas para servicio 3:")
for cr in cronos:
    print(cr)
    # count guardias for this cronograma
    cursor.execute("SELECT COUNT(*), MIN(fecha), MAX(fecha) FROM guardias WHERE cronograma_id = ? AND servicio_id = 3;", (cr[0],))
    print("  Guardias info:", cursor.fetchone())

print("\n--- DETALLE DE ALGUNAS GUARDIAS RECIENTES PARA SERVICIO 3 ---")
cursor.execute("""
    SELECT g.fecha, g.nombre, g.turno, g.horas, g.es_finde
    FROM guardias g
    WHERE g.servicio_id = 3
    ORDER BY g.fecha DESC, g.nombre
    LIMIT 20;
""")
for row in cursor.fetchall():
    print(row)

conn.close()
