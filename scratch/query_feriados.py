import sqlite3

conn = sqlite3.connect('cronograma_inteligente.db')
c = conn.cursor()

c.execute("SELECT id, fecha_inicio, fecha_fin, creado_en, notas, estado, tipo, servicio_id FROM cronogramas WHERE creado_en LIKE '2026-05-21%'")
rows = c.fetchall()
print("Cronogramas creados el 2026-05-21:")
for r in rows:
    print(f"ID: {r[0]} | Inicio: {r[1]} | Fin: {r[2]} | Creado: {r[3]} | Notas: {r[4]} | Estado: {r[5]} | Tipo: {r[6]} | Servicio: {r[7]}")
