import sqlite3
conn = sqlite3.connect("cronograma_inteligente.db")
print("=== TURNOS DETAIL ===")
rows = conn.execute("SELECT id, nombre, hora_inicio, horas, orden, activo, puesto_id FROM turnos_config WHERE servicio_id = 2").fetchall()
for r in rows:
    print(r)
conn.close()
