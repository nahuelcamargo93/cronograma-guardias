import sqlite3

DB_PATH = "cronograma_inteligente.db"
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

print("--- CRONOGRAMAS QUE CUBREN JUNIO 2026 ---")
cursor.execute("""
    SELECT DISTINCT c.id, c.fecha_inicio, c.fecha_fin, c.estado, c.notas
    FROM cronogramas c
    JOIN guardias g ON c.id = g.cronograma_id
    WHERE g.servicio_id = 3 AND (c.fecha_inicio LIKE '2026-06-%' OR c.fecha_fin LIKE '2026-06-%' OR (c.fecha_inicio <= '2026-06-30' AND c.fecha_fin >= '2026-06-01'));
""")
cronos = cursor.fetchall()
for cr in cronos:
    print(cr)
    cursor.execute("SELECT COUNT(*), MIN(fecha), MAX(fecha) FROM guardias WHERE cronograma_id = ? AND servicio_id = 3;", (cr[0],))
    print("  Guardias info:", cursor.fetchone())

print("\n--- TURNOS CONFIG PARA SERVICIO 3 ---")
cursor.execute("SELECT nombre, horas, puesto_id FROM turnos_config WHERE servicio_id = 3 AND activo = 1;")
for row in cursor.fetchall():
    print(row)

print("\n--- DETALLES DE ROLES PARA LOS SOLICITADOS ---")
solicitados = [
    "Arias, Guillermina",
    "Baracat, Denisse",
    "Mora, Sergio Enrique",
    "Noriega, Claudio Martín",
    "Zeballos, Valeria Alejandra",
    "Pacheco, Celeste",
    "Diaz Villafañe Morales, Abigail",
    "Nesteruk, María Silvia",
    "Quiroga Sassu, Maria Macarena",
    "Sánchez Reinoso, Ana Belén",
    "Villegas Oliva, Maria Belén"
]
for p in solicitados:
    cursor.execute("SELECT nombre, rol, categoria, activo FROM personal WHERE nombre LIKE ?;", (f"{p.split(',')[0]}%",))
    print(cursor.fetchall())

conn.close()
