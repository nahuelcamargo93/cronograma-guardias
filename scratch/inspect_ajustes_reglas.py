import sqlite3
conn = sqlite3.connect("cronograma_inteligente.db")
conn.row_factory = sqlite3.Row

print("--- REGULAS AJUSTES IN JUNE 2026 ---")
cur = conn.execute("""
    SELECT pra.* FROM personal_reglas_ajustes pra
    JOIN personal p ON pra.personal_nombre = p.nombre
    WHERE p.servicio_id = 4 
      AND pra.fecha_inicio <= '2026-06-30' 
      AND pra.fecha_fin >= '2026-06-01'
""")
for r in cur:
    print(dict(r))
conn.close()
