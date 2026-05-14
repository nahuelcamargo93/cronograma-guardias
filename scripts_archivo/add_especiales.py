import sqlite3
conn = sqlite3.connect('cronograma_inteligente.db')

turnos = {n: i for i, n in conn.execute('SELECT id, nombre FROM turnos_config WHERE servicio_id = 1').fetchall()}
id_m_esp = turnos.get('Ma\xf1ana_especial')
id_t_esp = turnos.get('Tarde_especial')
print(f'IDs - Manana_especial: {id_m_esp} | Tarde_especial: {id_t_esp}')

nuevos = [
    ('2026-06-01', '2026-06-07', id_m_esp, 0, None),
    ('2026-06-01', '2026-06-07', id_t_esp, 0, None),
    ('2026-06-08', '2026-06-14', id_m_esp, 0, None),
    ('2026-06-08', '2026-06-14', id_t_esp, 0, None),
]
for fi, ff, t_id, vac, d in nuevos:
    conn.execute(
        'INSERT INTO turnos_ajustes (turno_config_id, fecha_inicio, fecha_fin, vacantes, dias_semana) VALUES (?,?,?,?,?)',
        (t_id, fi, ff, vac, d)
    )

conn.commit()

print('\nAjustes especiales en DB:')
rows = conn.execute(
    'SELECT ta.fecha_inicio, ta.fecha_fin, tc.nombre, ta.vacantes '
    'FROM turnos_ajustes ta JOIN turnos_config tc ON ta.turno_config_id = tc.id '
    'WHERE tc.nombre LIKE "%especial%" ORDER BY ta.fecha_inicio'
).fetchall()
for r in rows:
    print(f'  {r[0]} -> {r[1]} | {r[2]:<18} | vac={r[3]}')

conn.close()
