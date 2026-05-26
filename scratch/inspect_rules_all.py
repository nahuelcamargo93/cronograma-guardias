import sqlite3
conn = sqlite3.connect("cronograma_inteligente.db")
conn.row_factory = sqlite3.Row

print("--- PERSONAL RULES FOR SERVICE 4 ---")
cur = conn.execute("""
    SELECT pr.*, p.rol, p.categoria 
    FROM personal_reglas pr
    JOIN personal p ON pr.personal_nombre = p.nombre
    WHERE p.servicio_id = 4
""")
for r in cur:
    print(dict(r))
conn.close()
