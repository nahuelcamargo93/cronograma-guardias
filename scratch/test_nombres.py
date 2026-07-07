import sqlite3

db_path = "c:\\Users\\asus\\Desktop\\Ryoko\\cronograma_inteligente\\cronograma_inteligente.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("=== REGLAS DE SERVICIO 3 ===")
rows = cursor.execute("""
    SELECT codigo_regla, parametros_json, activo
    FROM servicios_reglas
    WHERE servicio_id = 3 AND activo = 1
""").fetchall()

for r in rows:
    print(f"Regla: {r[0]} | Params: {r[1]} | Activo: {r[2]}")

print("\n=== REGLAS AJUSTES DE SERVICIO 3 ===")
rows_aj = cursor.execute("""
    SELECT codigo_regla, fecha_inicio, fecha_fin, accion, parametros_json
    FROM servicios_reglas_ajustes
    WHERE servicio_id = 3 AND activo = 1
""").fetchall()

for r in rows_aj:
    print(f"Regla: {r[0]} | Inicio: {r[1]} | Fin: {r[2]} | Accion: {r[3]} | Params: {r[4]}")

conn.close()
