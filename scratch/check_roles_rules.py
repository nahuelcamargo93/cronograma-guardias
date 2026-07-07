import sqlite3
conn = sqlite3.connect('cronograma_inteligente.db')

print("=== REGLAS DEL ROL 'Coordinador UCO' ===")
for r in conn.execute("SELECT codigo_regla, parametros_json FROM roles_reglas WHERE rol = 'Coordinador UCO'").fetchall():
    print(f"  {r[0]}: {r[1][:120]}...")

print("\n=== REGLAS DEL ROL 'Jefe' ===")
for r in conn.execute("SELECT codigo_regla, parametros_json FROM roles_reglas WHERE rol = 'Jefe'").fetchall():
    print(f"  {r[0]}: {r[1][:120]}...")

print("\n=== REGLAS DEL ROL 'Coordinador UTI' ===")
for r in conn.execute("SELECT codigo_regla, parametros_json FROM roles_reglas WHERE rol = 'Coordinador UTI'").fetchall():
    print(f"  {r[0]}: {r[1][:120]}...")
