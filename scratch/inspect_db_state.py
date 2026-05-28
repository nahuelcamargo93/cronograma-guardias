import sqlite3, json

con = sqlite3.connect('cronograma_inteligente.db')
cur = con.cursor()

print('=== TURNOS para servicio 3 ===')
cur.execute("SELECT tc.nombre, tc.hora_inicio, tc.horas FROM turnos_config tc WHERE tc.servicio_id=3 ORDER BY tc.nombre")
for row in cur.fetchall():
    print(f'  {row[0]}: inicio={row[1]}, horas={row[2]}')

print()
print('=== PUESTOS ===')
cur.execute("SELECT id, nombre FROM puestos")
for row in cur.fetchall():
    print(f'  id={row[0]}, nombre={row[1]}')

print()
print('=== DEMANDA servicio 3 (via puesto_id) ===')
cur.execute("""SELECT dc.tipo_dia, dc.hora_inicio, dc.hora_fin, pu.nombre as puesto, dc.cantidad_min, dc.cantidad_max 
               FROM demanda_config dc 
               JOIN puestos pu ON dc.puesto_id=pu.id
               WHERE dc.servicio_id=3 
               ORDER BY dc.tipo_dia, dc.hora_inicio""")
for row in cur.fetchall():
    print(f'  {row[0]} {row[1]}-{row[2]}: puesto={row[3]}, min={row[4]}, max={row[5]}')

print()
print('=== personal_reglas con EXACTO_FINDE_Y_DIA (suspensiones) ===')
cur.execute("SELECT personal_nombre, parametros_json, fecha_inicio, fecha_fin FROM personal_reglas WHERE codigo_regla='EXACTO_FINDE_Y_DIA'")
for row in cur.fetchall():
    print(f'  {row[0]}: params={row[1]}, desde={row[2]}, hasta={row[3]}')

print()
print('=== COUNT personal servicio 3 ===')
cur.execute("""SELECT COUNT(*), pu.nombre 
               FROM personal pi 
               JOIN personal_puestos pp ON pi.id=pp.personal_id 
               JOIN puestos pu ON pp.puesto_id=pu.id 
               WHERE pi.servicio_id=3 
               GROUP BY pu.nombre""")
for row in cur.fetchall():
    print(f'  {row[1]}: {row[0]} personas')

print()
print('=== personal_reglas con MIN_HORAS_MES_CALENDARIO para servicio 3 ===')
cur.execute("""SELECT pr.personal_nombre, pr.parametros_json, pr.fecha_inicio, pr.fecha_fin 
               FROM personal_reglas pr 
               JOIN personal pi ON pr.personal_nombre = pi.nombre 
               WHERE pi.servicio_id=3 AND pr.codigo_regla='MIN_HORAS_MES_CALENDARIO'
               LIMIT 10""")
for row in cur.fetchall():
    print(f'  {row[0]}: params={row[1]}, desde={row[2]}, hasta={row[3]}')

con.close()
