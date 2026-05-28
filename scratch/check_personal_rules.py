import sqlite3, json

con = sqlite3.connect('cronograma_inteligente.db')
cur = con.cursor()

print("=== REGLAS PERSONAL (personal_reglas) para Servicio 3 ===")
cur.execute("""
    SELECT pr.personal_nombre, pr.codigo_regla, pr.activo, pr.parametros_json 
    FROM personal_reglas pr
    JOIN personal p ON pr.personal_nombre = p.nombre
    WHERE p.servicio_id = 3
    ORDER BY pr.personal_nombre, pr.codigo_regla
""")
for r in cur.fetchall():
    print(f"  {r[0]} | {r[1]} | Activo: {r[2]} | Params: {r[3]}")

print("\n=== AJUSTES REGLAS PERSONAL (personal_reglas_ajustes) para Servicio 3 ===")
cur.execute("""
    SELECT pra.personal_nombre, pra.codigo_regla, pra.activo, pra.parametros_json, pra.fecha_inicio, pra.fecha_fin
    FROM personal_reglas_ajustes pra
    JOIN personal p ON pra.personal_nombre = p.nombre
    WHERE p.servicio_id = 3
    ORDER BY pra.personal_nombre, pra.codigo_regla
""")
for r in cur.fetchall():
    print(f"  {r[0]} | {r[1]} | Activo: {r[2]} | Params: {r[3]} | {r[4]} a {r[5]}")

con.close()
