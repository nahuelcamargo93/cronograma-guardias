import sqlite3
conn = sqlite3.connect("cronograma_inteligente.db")
cursor = conn.cursor()

print("--- TURNOS CONFIG (servicio 4) ---")
turnos = cursor.execute("SELECT id, nombre, horas, hora_inicio, puesto_id, activo FROM turnos_config WHERE servicio_id = 4").fetchall()
for t in turnos:
    print(t)

print("\n--- PUESTOS (servicio 4) ---")
puestos = cursor.execute("SELECT id, nombre FROM puestos WHERE servicio_id = 4").fetchall()
for p in puestos:
    print(p)
    
conn.close()
