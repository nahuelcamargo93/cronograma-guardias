import sqlite3

DB_PATH = "c:/Users/asus/Desktop/Ryoko/cronograma_inteligente/cronograma_inteligente.db"
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

print("=== Columnas de personal ===")
cursor.execute("PRAGMA table_info(personal)")
for col in cursor.fetchall():
    print(col)

print("\n=== Personal del Servicio 2 ===")
pers = cursor.execute("SELECT nombre FROM personal WHERE servicio_id = 2 ORDER BY nombre").fetchall()
for p in pers:
    print(f"Nombre: {p[0]}")

print("\n=== Todos los Francos Forzados en Servicio 2 en Julio 2026 ===")
rows = cursor.execute("""
    SELECT personal_nombre, fecha_inicio, fecha_fin, accion, activo, parametros_json
    FROM personal_reglas_ajustes
    WHERE codigo_regla = 'FRANCO_FORZADO'
      AND fecha_inicio >= '2026-07-01'
    ORDER BY personal_nombre, fecha_inicio
""").fetchall()

for r in rows:
    print(f"Profesional: {r[0]}, Fecha Inicio: {r[1]}, Fecha Fin: {r[2]}, Acción: {r[3]}, Activo: {r[4]}")

conn.close()



