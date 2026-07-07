import sqlite3
conn = sqlite3.connect('cronograma_inteligente.db')
print("=== Demanda Config (Servicio 2) ===")
q = """
SELECT dc.id, p.nombre as puesto_nombre, dc.tipo_dia, dc.hora_inicio, dc.hora_fin, dc.cantidad_min, dc.cantidad_max, dc.dias_semana
FROM demanda_config dc
JOIN puestos p ON dc.puesto_id = p.id
WHERE p.servicio_id = 2
"""
rows = conn.execute(q).fetchall()
for r in rows:
    print(r)

print("\n=== Turnos Config (Servicio 2) ===")
q2 = """
SELECT tc.id, tc.nombre, tc.hora_inicio, tc.horas, tc.sigla, tc.puesto_id
FROM turnos_config tc
WHERE tc.servicio_id = 2
"""
rows2 = conn.execute(q2).fetchall()
for r in rows2:
    print(r)
conn.close()
