import sqlite3

conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()

print("--- Cronograma 492 ---")
cursor.execute("SELECT * FROM cronogramas WHERE id = 492")
crono = cursor.fetchone()
print(crono)

if crono:
    print("\n--- Guardias en Cronograma 492 ---")
    cursor.execute("SELECT nombre, fecha, turno, horas, es_finde FROM guardias WHERE cronograma_id = 492 ORDER BY fecha, nombre")
    guardias = cursor.fetchall()
    print(f"Total guardias: {len(guardias)}")
    for g in guardias:
        print(g)
else:
    print("Cronograma 492 no encontrado.")

conn.close()
