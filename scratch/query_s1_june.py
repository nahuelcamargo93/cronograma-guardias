import sqlite3

DB_PATH = "cronograma_inteligente.db"
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

print("--- BUSCAR PROFESIONALES EN SERVICIO 1 ---")
cursor.execute("SELECT nombre, rol, categoria, activo FROM personal WHERE servicio_id = 1 AND (nombre LIKE '%Leonforte%' OR nombre LIKE '%Guardia%');")
for row in cursor.fetchall():
    print(row)

print("\n--- CRONOGRAMAS EXISTENTES PARA SERVICIO 1 EN JUNIO 2026 ---")
cursor.execute("""
    SELECT DISTINCT c.id, c.fecha_inicio, c.fecha_fin, c.estado, c.notas
    FROM cronogramas c
    JOIN guardias g ON c.id = g.cronograma_id
    WHERE g.servicio_id = 1 AND (c.fecha_inicio LIKE '2026-06-%' OR c.fecha_fin LIKE '2026-06-%' OR (c.fecha_inicio <= '2026-06-30' AND c.fecha_fin >= '2026-06-01'));
""")
for row in cursor.fetchall():
    print(row)

print("\n--- CONFIGURACION DE TURNOS DE NOCHE EN SERVICIO 1 ---")
cursor.execute("SELECT nombre, horas, activo, dias_semana FROM turnos_config WHERE servicio_id = 1 AND nombre LIKE '%Noche%';")
for row in cursor.fetchall():
    print(row)

conn.close()
