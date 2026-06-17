import sqlite3

conn = sqlite3.connect("cronograma_inteligente.db")
cursor = conn.cursor()

print("=== Cronograma 305 ===")
cursor.execute("SELECT id, fecha_inicio, fecha_fin, creado_en, notas, estado FROM cronogramas WHERE id = 305")
row = cursor.fetchone()
if row:
    print(row)
else:
    print("No se encontró el cronograma 305")
    conn.close()
    exit()

print("\n=== Feriados en el rango del Cronograma 305 ===")
fecha_inicio, fecha_fin = row[1], row[2]
cursor.execute("SELECT fecha, descripcion FROM feriados WHERE fecha BETWEEN ? AND ?", (fecha_inicio, fecha_fin))
for f in cursor.fetchall():
    print(f)

print("\n=== Exclusiones de feriados para Servicio 1 ===")
cursor.execute("SELECT fecha FROM feriados_exclusiones WHERE servicio_id = 1 AND fecha BETWEEN ? AND ?", (fecha_inicio, fecha_fin))
for f in cursor.fetchall():
    print(f)

print("\n=== Guardias asignadas en el cronograma 305 (Muestra 20) ===")
cursor.execute("""
    SELECT fecha, turno, nombre, horas, es_finde 
    FROM guardias 
    WHERE cronograma_id = 305 
    ORDER BY fecha, turno
    LIMIT 20
""")
for g in cursor.fetchall():
    print(g)

print("\n=== Conteo de guardias por día en el cronograma 305 ===")
cursor.execute("""
    SELECT fecha, COUNT(*) 
    FROM guardias 
    WHERE cronograma_id = 305 
    GROUP BY fecha 
    ORDER BY fecha
""")
for c in cursor.fetchall():
    print(c)

conn.close()
