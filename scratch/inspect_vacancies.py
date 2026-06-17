import sqlite3

conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()

# Ver los ajustes de turnos para D_Planta y N_Planta (Servicio 3) en Julio 2026
print("=== AJUSTES DE TURNOS EN JULIO ===")
cursor.execute("""
    SELECT ta.id, tc.nombre, ta.fecha_inicio, ta.fecha_fin, ta.vacantes, ta.dias_semana
    FROM turnos_ajustes ta
    JOIN turnos_config tc ON ta.turno_config_id = tc.id
    WHERE tc.servicio_id = 3 AND ta.activo = 1
      AND ((ta.fecha_inicio BETWEEN '2026-07-01' AND '2026-07-31') 
           OR (ta.fecha_fin BETWEEN '2026-07-01' AND '2026-07-31')
           OR (ta.fecha_inicio <= '2026-07-01' AND ta.fecha_fin >= '2026-07-31'))
""")
for ta in cursor.fetchall():
    print(ta)

# Ver las reglas de Garcia Rodriguez, Maria Eugenia.
print("\n=== REGLAS DE GARCIA RODRIGUEZ ===")
cursor.execute("""
    SELECT pr.id, pr.codigo_regla, pr.parametros_json 
    FROM personal_reglas pr
    WHERE pr.personal_nombre LIKE '%Garcia Rodriguez%'
""")
for pr in cursor.fetchall():
    print(pr)

# Ver los ajustes de reglas de Garcia Rodriguez en Julio 2026
print("\n=== AJUSTES DE REGLAS DE GARCIA RODRIGUEZ EN JULIO ===")
cursor.execute("""
    SELECT id, codigo_regla, fecha_inicio, fecha_fin, accion, parametros_json
    FROM personal_reglas_ajustes
    WHERE personal_nombre LIKE '%Garcia Rodriguez%'
      AND ((fecha_inicio BETWEEN '2026-07-01' AND '2026-07-31') 
           OR (fecha_fin BETWEEN '2026-07-01' AND '2026-07-31')
           OR (fecha_inicio <= '2026-07-01' AND fecha_fin >= '2026-07-31'))
""")
for a in cursor.fetchall():
    print(a)

conn.close()
