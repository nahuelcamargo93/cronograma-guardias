import sqlite3

conn = sqlite3.connect("cronograma_inteligente.db")
print("=== personal_reglas for BORIA MAYRA ===")
for r in conn.execute("SELECT * FROM personal_reglas WHERE personal_nombre = 'BORIA MAYRA'").fetchall():
    print(r)

print("=== personal_reglas_ajustes for BORIA MAYRA ===")
for r in conn.execute("SELECT * FROM personal_reglas_ajustes WHERE personal_nombre = 'BORIA MAYRA'").fetchall():
    print(r)

print("=== personal_puestos for BORIA MAYRA ===")
for r in conn.execute("""
    SELECT pp.*, p.nombre 
    FROM personal_puestos pp 
    JOIN puestos p ON pp.puesto_id = p.id 
    WHERE pp.personal_nombre = 'BORIA MAYRA'
""").fetchall():
    print(r)

conn.close()
