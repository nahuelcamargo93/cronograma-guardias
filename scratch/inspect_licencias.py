import sqlite3
conn = sqlite3.connect("cronograma_inteligente.db")
conn.row_factory = sqlite3.Row

print("--- LICENCIAS FOR SERVICE 4 IN JUNE 2026 ---")
cur = conn.execute("""
    SELECT l.* FROM licencias l
    JOIN personal p ON l.nombre = p.nombre
    WHERE p.servicio_id = 4 
      AND l.fecha_inicio <= '2026-06-30' 
      AND l.fecha_fin >= '2026-06-01'
""")
for r in cur:
    print(dict(r))
conn.close()
