import sqlite3

conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()

print("=== PUESTOS DEL SERVICIO 3 ===")
cursor.execute("SELECT id, nombre FROM puestos WHERE servicio_id = 3")
puestos = cursor.fetchall()
puestos_ids = [p[0] for p in puestos]
for p in puestos:
    print(p)

print("\n=== DEMANDA CONFIG SERVICIO 3 ===")
for p_id in puestos_ids:
    cursor.execute("""
        SELECT dc.id, p.nombre, dc.tipo_dia, dc.hora_inicio, dc.hora_fin, dc.cantidad_min, dc.cantidad_max, dc.dias_semana
        FROM demanda_config dc
        JOIN puestos p ON dc.puesto_id = p.id
        WHERE dc.puesto_id = ? AND dc.activo = 1
    """, (p_id,))
    for dc in cursor.fetchall():
        print(dc)

print("\n=== DEMANDA AJUSTES SERVICIO 3 EN JULIO ===")
cursor.execute("""
    SELECT da.id, p.nombre, da.fecha_inicio, da.fecha_fin, da.cantidad_min, da.cantidad_max, da.dias_semana
    FROM demanda_ajustes da
    JOIN demanda_config dc ON da.demanda_config_id = dc.id
    JOIN puestos p ON dc.puesto_id = p.id
    WHERE dc.puesto_id IN ({}) AND da.activo = 1
      AND ((da.fecha_inicio BETWEEN '2026-07-01' AND '2026-07-31') 
           OR (da.fecha_fin BETWEEN '2026-07-01' AND '2026-07-31')
           OR (da.fecha_inicio <= '2026-07-01' AND da.fecha_fin >= '2026-07-31'))
""".format(",".join(map(str, puestos_ids))))
for da in cursor.fetchall():
    print(da)

conn.close()
