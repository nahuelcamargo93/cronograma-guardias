import sqlite3
import json

conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()

# Buscar el ID de Aguilera Graciela y su servicio
cursor.execute("SELECT nombre, servicio_id FROM personal WHERE nombre LIKE '%Aguilera%'")
empleados = cursor.fetchall()
print("Empleados encontrados:")
for emp in empleados:
    print(emp)

# Si hay empleados, buscar sus reglas
if empleados:
    emp_nombre = empleados[0][0]
    cursor.execute("""
        SELECT pr.id, pr.codigo_regla, pr.parametros_json 
        FROM personal_reglas pr
        WHERE pr.personal_nombre = ?
    """, (emp_nombre,))
    print(f"\nReglas para {emp_nombre}:")
    for r in cursor.fetchall():
        print(r)
        
    cursor.execute("""
        SELECT pra.id, pra.codigo_regla, pra.fecha_inicio, pra.fecha_fin, pra.accion, pra.parametros_json
        FROM personal_reglas_ajustes pra
        WHERE pra.personal_nombre = ?
    """, (emp_nombre,))
    print(f"\nAjustes de reglas para {emp_nombre}:")
    for a in cursor.fetchall():
        print(a)

# Buscar turnos del Servicio 3
print("\nTurnos del Servicio 3:")
cursor.execute("""
    SELECT nombre, hora_inicio, horas, dias_semana 
    FROM turnos_config 
    WHERE servicio_id = 3
""")
for t in cursor.fetchall():
    print(t)

# Buscar licencias de Aguilera Graciela en Julio 2026
print("\nLicencias de Aguilera Graciela (entre 2026-07-01 y 2026-07-31):")
cursor.execute("""
    SELECT nombre, tipo, fecha_inicio, fecha_fin 
    FROM licencias 
    WHERE nombre = 'Aguilera Graciela' 
      AND ((fecha_inicio BETWEEN '2026-07-01' AND '2026-07-31') 
           OR (fecha_fin BETWEEN '2026-07-01' AND '2026-07-31')
           OR (fecha_inicio <= '2026-07-01' AND fecha_fin >= '2026-07-31'))
""")
for l in cursor.fetchall():
    print(l)

# Consultar si hay algún ajuste específico de Aguilera Graciela en Julio 2026
print("\nAjustes de reglas para Aguilera Graciela en Julio 2026:")
cursor.execute("""
    SELECT id, codigo_regla, fecha_inicio, fecha_fin, accion, parametros_json
    FROM personal_reglas_ajustes
    WHERE personal_nombre = 'Aguilera Graciela'
      AND ((fecha_inicio BETWEEN '2026-07-01' AND '2026-07-31') 
           OR (fecha_fin BETWEEN '2026-07-01' AND '2026-07-31')
           OR (fecha_inicio <= '2026-07-01' AND fecha_fin >= '2026-07-31'))
""")
for a in cursor.fetchall():
    print(a)


conn.close()
