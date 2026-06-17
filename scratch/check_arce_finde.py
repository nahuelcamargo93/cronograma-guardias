import sqlite3
conn = sqlite3.connect('cronograma_inteligente.db')
conn.row_factory = sqlite3.Row

print('=== MANEJO_FINDES en servicio 3 ===')
r = conn.execute("SELECT codigo_regla, activo, parametros_json FROM servicios_reglas WHERE servicio_id = 3 AND codigo_regla = 'MANEJO_FINDES'").fetchone()
print(dict(r) if r else 'NO EXISTE')

print()
print('=== EXACTO_FINDE_Y_DIA en servicio 3 ===')
r = conn.execute("SELECT codigo_regla, activo, parametros_json FROM servicios_reglas WHERE servicio_id = 3 AND codigo_regla = 'EXACTO_FINDE_Y_DIA'").fetchone()
print(dict(r) if r else 'NO EXISTE')

print()
print('=== Reglas personales de Arce, Carolina ===')
for r in conn.execute("SELECT codigo_regla, activo, parametros_json FROM personal_reglas WHERE personal_nombre = 'Arce, Carolina'").fetchall():
    print(dict(r))

print()
print('=== Guardias de Arce en crono 505 ===')
for r in conn.execute("""
    SELECT g.fecha, g.turno, strftime('%w', g.fecha) as dow
    FROM guardias g
    WHERE g.cronograma_id = 505 AND g.nombre = 'Arce, Carolina'
    ORDER BY g.fecha
""").fetchall():
    dow = int(dict(r)['dow'])
    es_finde = '**FINDE**' if dow in (0, 6) else ''
    print(dict(r), es_finde)

conn.close()
