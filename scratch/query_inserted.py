import sqlite3

DB_PATH = "cronograma_inteligente.db"
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

print("--- CRONOGRAMA INSERTADO ---")
cursor.execute("SELECT id, fecha_inicio, fecha_fin, creado_en, notas, estado FROM cronogramas WHERE id = 492;")
print(cursor.fetchone())

print("\n--- GUARDIAS INSERTADAS EN CRONOGRAMA 492 ---")
cursor.execute("""
    SELECT fecha, nombre, turno, horas, es_finde, servicio_id
    FROM guardias
    WHERE cronograma_id = 492
    ORDER BY fecha, nombre;
""")
for row in cursor.fetchall():
    print(row)

conn.close()
