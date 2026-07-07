import sqlite3
conn = sqlite3.connect('cronograma_inteligente.db')
nombres = ['Garcia, Luciano', 'Franco, Leandro', 'Moyano, Fernando', 'Toledo, Andrea', 'Camargo, Nahuel', 'Giacoppo, Veronica', 'Coniglio, Melisa']
placeholders = ','.join(['?']*len(nombres))
rows = conn.execute(f'''
    SELECT pp.personal_nombre, pu.nombre AS puesto, p.rol
    FROM personal_puestos pp
    JOIN personal p ON pp.personal_nombre = p.nombre AND pp.servicio_id = p.servicio_id
    JOIN puestos pu ON pp.puesto_id = pu.id
    WHERE pp.servicio_id = 1 AND pp.personal_nombre IN ({placeholders})
''', nombres).fetchall()
for r in rows:
    print(r)
if not rows:
    print("SIN PUESTOS CONFIGURADOS")
