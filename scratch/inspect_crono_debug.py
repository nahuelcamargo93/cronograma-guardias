import sqlite3

conn = sqlite3.connect("cronograma_inteligente.db")
print("=== cronograma 261 ===")
crono = conn.execute("SELECT id, fecha_inicio, fecha_fin, notas FROM cronogramas WHERE id = 261").fetchone()
print(crono)

print("=== infracciones_debug for cronograma 261 ===")
infr = conn.execute("SELECT * FROM infracciones_debug WHERE cronograma_id = 261").fetchall()
print(f"Total violations in DB: {len(infr)}")
for i in infr:
    print(i)
    
conn.close()
