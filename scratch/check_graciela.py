import sqlite3
import json

conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()

print("--- Guardias de PALANA GRACIELA a fin de Julio ---")
rows = cursor.execute("""
    SELECT g.id, g.cronograma_id, g.nombre, g.fecha, g.turno, g.horas
    FROM guardias g
    WHERE g.nombre = 'PALANA GRACIELA' AND g.fecha BETWEEN '2026-07-25' AND '2026-07-31'
""").fetchall()
for r in rows:
    print(r)

print("\n--- Francos forzados de PALANA GRACIELA en agosto ---")
rows_ff = cursor.execute("""
    SELECT * FROM personal_francos_forzados
    WHERE personal_nombre = 'PALANA GRACIELA'
""").fetchall()
for r in rows_ff:
    print(r)

print("\n--- Reglas de servicio para MANEJO_FINDES (Servicio 2) ---")
rows_rf = cursor.execute("""
    SELECT codigo_regla, parametros_json
    FROM servicios_reglas
    WHERE servicio_id = 2 AND codigo_regla = 'MANEJO_FINDES'
""").fetchall()
for r in rows_rf:
    print(r[0])
    print(json.dumps(json.loads(r[1]), indent=2))
conn.close()
