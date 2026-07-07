import sqlite3
conn = sqlite3.connect('cronograma_inteligente.db')
conn.row_factory = sqlite3.Row
turnos = conn.execute('SELECT nombre, sum(horas) as total_horas FROM guardias WHERE cronograma_id = 534 GROUP BY nombre').fetchall()
for t in turnos:
    print(f"{t['nombre']}: {t['total_horas']}h")
