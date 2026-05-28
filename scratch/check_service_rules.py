import sqlite3, json

con = sqlite3.connect('cronograma_inteligente.db')
cur = con.cursor()

print("=== SERVICIOS REGLAS para Servicio 3 ===")
cur.execute("""
    SELECT codigo_regla, activo, parametros_json 
    FROM servicios_reglas 
    WHERE servicio_id = 3
    ORDER BY codigo_regla
""")
for r in cur.fetchall():
    print(f"  {r[0]} | Activo: {r[1]} | Params: {r[2]}")
con.close()
