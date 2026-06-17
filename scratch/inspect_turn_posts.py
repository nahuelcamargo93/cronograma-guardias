import sqlite3

conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()

print("--- Turnos Config del servicio_id = 2 ---")
cursor.execute("""
    SELECT tc.nombre, tc.puesto_id, p.nombre 
    FROM turnos_config tc
    LEFT JOIN puestos p ON tc.puesto_id = p.id
    WHERE tc.servicio_id = 2
""")
for r in cursor.fetchall():
    print(r)

conn.close()
