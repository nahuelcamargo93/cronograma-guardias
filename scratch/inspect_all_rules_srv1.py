import sqlite3

db_path = r"c:\Users\asus\Desktop\Ryoko\cronograma_inteligente\cronograma_inteligente.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("--- Reglas en personal_reglas para servicio_id = 1 ---")
cursor.execute("""
    SELECT pr.personal_nombre, pr.codigo_regla, pr.parametros_json, pr.activo 
    FROM personal_reglas pr
    JOIN personal p ON pr.personal_nombre = p.nombre
    WHERE p.servicio_id = 1 AND pr.activo = 1
""")
for r in cursor.fetchall():
    print(r)

print("\n--- Ajustes de reglas de personal (personal_reglas_ajustes) para servicio_id = 1 ---")
cursor.execute("""
    SELECT pra.personal_nombre, pra.codigo_regla, pra.fecha_inicio, pra.fecha_fin, pra.accion, pra.parametros_json, pra.activo
    FROM personal_reglas_ajustes pra
    JOIN personal p ON pra.personal_nombre = p.nombre
    WHERE p.servicio_id = 1 AND pra.activo = 1
""")
for r in cursor.fetchall():
    print(r)

print("\n--- Ajustes de reglas de servicio (servicios_reglas_ajustes) para servicio_id = 1 ---")
cursor.execute("""
    SELECT * FROM servicios_reglas_ajustes WHERE servicio_id = 1 AND activo = 1
""")
for r in cursor.fetchall():
    print(r)

conn.close()
