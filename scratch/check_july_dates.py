import sqlite3

conn = sqlite3.connect('cronograma_inteligente.db')

try:
    crono_base = 583
    n_winners = ['BORIA MAYRA', 'GUIÑAZU KARINA', 'MAÑE LORENA', 'MONDONE PAULA', 'NIEVAS CARLA', 'ORTIZ LAURA', 'ROJAS JULIANA', 'VELIZ LIONEL']

    q = """
    SELECT DISTINCT nombre, fecha, turno, horas
    FROM guardias
    WHERE servicio_id = 2
      AND cronograma_id = ?
      AND fecha >= '2026-07-27'
      AND fecha < '2026-08-01'
      AND nombre IN ({})
    ORDER BY nombre, fecha
    """.format(",".join(f"'{n}'" for n in n_winners))

    rows = conn.execute(q, (crono_base,)).fetchall()
    for r in rows:
        print(r)

finally:
    conn.close()
