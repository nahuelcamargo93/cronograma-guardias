import sqlite3
conn = sqlite3.connect("cronograma_inteligente.db")
conn.row_factory = sqlite3.Row

print("--- REGLAS ASOCIADAS AL SERVICIO 2 (Enfermeria) ---")
cur = conn.execute("""
    SELECT * FROM servicios_reglas WHERE servicio_id = 2
""")
for r in cur:
    print(dict(r))

conn.close()
