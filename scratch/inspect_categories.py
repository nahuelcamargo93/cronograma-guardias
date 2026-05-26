import sqlite3
conn = sqlite3.connect("cronograma_inteligente.db")
conn.row_factory = sqlite3.Row

print("--- PERSONAL BY CATEGORY AND ROLE (COM - Servicio 4) ---")
cur = conn.execute("""
    SELECT categoria, rol, COUNT(*) as cnt 
    FROM personal 
    WHERE servicio_id = 4 AND activo = 1 
    GROUP BY categoria, rol
""")
for r in cur:
    print(dict(r))

print("\n--- DEMANDA CONFIG (MIN vs MAX) BY SHIFT AND PUESTO ---")
cur = conn.execute("""
    SELECT dc.tipo_dia, dc.hora_inicio, dc.hora_fin, p.nombre as puesto, dc.cantidad_min, dc.cantidad_max
    FROM demanda_config dc
    JOIN puestos p ON dc.puesto_id = p.id
    WHERE p.servicio_id = 4 AND dc.activo = 1
    ORDER BY dc.tipo_dia, dc.hora_inicio, puesto
""")
for r in cur:
    print(dict(r))

conn.close()
