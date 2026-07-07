import sqlite3

conn = sqlite3.connect('cronograma_inteligente.db')

try:
    crono_base = 583
    q = """
    SELECT nombre, turno, horas
    FROM guardias
    WHERE servicio_id = 2
      AND cronograma_id = ?
      AND fecha = '2026-07-31'
    ORDER BY nombre
    """
    rows = conn.execute(q, (crono_base,)).fetchall()
    print(f"Total guardias on July 31: {len(rows)}")
    for r in rows:
        print(r)

finally:
    conn.close()
