import sqlite3, json

con = sqlite3.connect('cronograma_inteligente.db')
cur = con.cursor()

print("=== DEMANDA CONFIG (Servicio 3) ===")
cur.execute("SELECT * FROM demanda_config WHERE servicio_id=3")
for row in cur.fetchall():
    print(row)

print("\n=== REGLAS SERVICIO 3 ===")
cur.execute("SELECT codigo_regla, activo, parametros_json FROM servicios_reglas WHERE servicio_id=3")
for row in cur.fetchall():
    print(row)

print("\n=== REGLAS PERSONAL SERVICIO 3 ===")
cur.execute("SELECT personal_nombre, codigo_regla, activo, parametros_json FROM personal_reglas WHERE servicio_id=3")
for row in cur.fetchall():
    print(row)
