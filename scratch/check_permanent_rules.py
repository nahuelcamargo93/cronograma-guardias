import sqlite3

con = sqlite3.connect('cronograma_inteligente.db')
cur = con.cursor()

print("=== PERMANENT RULES IN personal_reglas for Service 3 ===")
cur.execute("""
    SELECT pr.personal_nombre, pr.codigo_regla, pr.activo, pr.parametros_json 
    FROM personal_reglas pr
    JOIN personal p ON pr.personal_nombre = p.nombre
    WHERE p.servicio_id = 3
    ORDER BY pr.personal_nombre, pr.codigo_regla
""")
for r in cur.fetchall():
    print(f"  {r[0]} | {r[1]} | Activo: {r[2]} | Params: {r[3]}")
con.close()
