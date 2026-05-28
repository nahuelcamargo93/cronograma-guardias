import sqlite3, json

con = sqlite3.connect('cronograma_inteligente.db')
cur = con.cursor()

print("=== TODAS LAS REGLAS SERVICIO 3 ===")
cur.execute("SELECT codigo_regla, parametros_json FROM servicios_reglas WHERE servicio_id=3 ORDER BY codigo_regla")
for r in cur.fetchall():
    print(f"  {r[0]}: {r[1]}")

print("\n=== REGLAS CATALOGO ACTIVAS EN SERVICIO 3 ===")
cur.execute("""
    SELECT sr.codigo_regla, sr.activo, rc.tipo 
    FROM servicios_reglas sr 
    JOIN reglas_catalogo rc ON sr.codigo_regla = rc.codigo_regla
    WHERE sr.servicio_id=3 
    ORDER BY rc.tipo, sr.codigo_regla
""")
for r in cur.fetchall():
    print(f"  [{r[2]}] {r[0]}: activo={r[1]}")

con.close()
