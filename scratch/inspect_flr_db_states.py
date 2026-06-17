import sqlite3

conn = sqlite3.connect("cronograma_inteligente.db")
print("=== reglas_catalogo ===")
for r in conn.execute("SELECT * FROM reglas_catalogo WHERE codigo_regla LIKE '%FINDE_LARGO%'").fetchall():
    print(r)

print("=== servicios_reglas for service 2 ===")
for r in conn.execute("SELECT * FROM servicios_reglas WHERE servicio_id = 2 AND codigo_regla LIKE '%FINDE_LARGO%'").fetchall():
    print(r)

print("=== personal_reglas for FLR ===")
for r in conn.execute("SELECT * FROM personal_reglas WHERE codigo_regla LIKE '%FINDE_LARGO%'").fetchall():
    print(r)

conn.close()
