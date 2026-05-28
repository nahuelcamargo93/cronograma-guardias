import sqlite3

con = sqlite3.connect('cronograma_inteligente.db')
cur = con.cursor()

print("=== SETTING cantidad_max TO 8 FOR PLANTA ===")
cur.execute("""
    UPDATE demanda_config 
    SET cantidad_max = 8 
    WHERE puesto_id = 10 AND activo = 1
""")
con.commit()

print("Verificando demanda_config:")
cur.execute("""
    SELECT dc.id, dc.tipo_dia, dc.hora_inicio, dc.cantidad_min, dc.cantidad_max, pu.nombre
    FROM demanda_config dc
    JOIN puestos pu ON dc.puesto_id = pu.id
    WHERE pu.servicio_id = 3
""")
for r in cur.fetchall():
    print(f"  [{r[1]}] {r[2]}: {r[5]} min={r[3]}, max={r[4]}")

con.close()
