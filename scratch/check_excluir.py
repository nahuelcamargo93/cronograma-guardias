import sqlite3, json

con = sqlite3.connect('cronograma_inteligente.db')
cur = con.cursor()

print("=== EXCLUIR_TURNOS en personal_reglas (Servicio 3) ===")
cur.execute("""
    SELECT pr.personal_nombre, pr.parametros_json
    FROM personal_reglas pr
    JOIN personal p ON pr.personal_nombre = p.nombre
    WHERE p.servicio_id = 3 AND pr.codigo_regla = 'EXCLUIR_TURNOS'
    ORDER BY pr.personal_nombre
""")
rows = cur.fetchall()
if rows:
    for r in rows:
        params = json.loads(r[1]) if r[1] else {}
        print(f"  {r[0]}: {params}")
else:
    print("  Ninguno en personal_reglas")

print("\n=== EXCLUIR_TURNOS en servicios_reglas (Servicio 3) ===")
cur.execute("SELECT parametros_json FROM servicios_reglas WHERE servicio_id=3 AND codigo_regla='EXCLUIR_TURNOS'")
row = cur.fetchone()
if row:
    print(f"  {row[0]}")
else:
    print("  No hay EXCLUIR_TURNOS a nivel de servicio")

print("\n=== EXCLUIR_TURNOS en personal_reglas_ajustes (Servicio 3) ===")
cur.execute("""
    SELECT pra.personal_nombre, pra.fecha_inicio, pra.fecha_fin, pra.accion, pra.parametros_json
    FROM personal_reglas_ajustes pra
    JOIN personal p ON pra.personal_nombre = p.nombre
    WHERE p.servicio_id = 3 AND pra.codigo_regla = 'EXCLUIR_TURNOS' AND pra.activo = 1
    ORDER BY pra.personal_nombre
""")
rows2 = cur.fetchall()
if rows2:
    for r in rows2:
        print(f"  {r[0]} ({r[1]} a {r[2]}): accion={r[3]}, params={r[4]}")
else:
    print("  Ninguno en personal_reglas_ajustes")

print("\n=== TODOS los turnos de Servicio 3 ===")
cur.execute("SELECT nombre, hora_inicio, horas FROM turnos_config WHERE servicio_id=3 ORDER BY nombre")
for r in cur.fetchall():
    print(f"  {r[0]}: {r[1]}, {r[2]}h")

con.close()
