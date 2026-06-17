import sqlite3
import json

conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()

cronograma_id = 252

print("=== CRONOGRAMA 252 ===")
cursor.execute("SELECT id, fecha_inicio, fecha_fin, notas FROM cronogramas WHERE id = ?", (cronograma_id,))
print("Cronograma:", cursor.fetchone())

# Guardias de Aguilera Graciela en el cronograma 252
cursor.execute("""
    SELECT fecha, turno, horas 
    FROM guardias 
    WHERE cronograma_id = ? AND nombre = 'Aguilera Graciela'
    ORDER BY fecha
""", (cronograma_id,))
print("\nGuardias de Aguilera Graciela en 252:")
guardias_emp = cursor.fetchall()
for g in guardias_emp:
    print(g)
print("Total horas asignadas:", sum(g[2] for g in guardias_emp))

# Todas las licencias de Aguilera Graciela en la base de datos
cursor.execute("""
    SELECT tipo, fecha_inicio, fecha_fin 
    FROM licencias 
    WHERE nombre = 'Aguilera Graciela'
    ORDER BY fecha_inicio
""")
print("\nTodas las licencias de Aguilera Graciela:")
for l in cursor.fetchall():
    print(l)

# Todos los ajustes de reglas de Aguilera Graciela
cursor.execute("""
    SELECT codigo_regla, fecha_inicio, fecha_fin, accion, parametros_json
    FROM personal_reglas_ajustes
    WHERE personal_nombre = 'Aguilera Graciela'
    ORDER BY fecha_inicio
""")
print("\nTodos los ajustes de reglas de Aguilera Graciela:")
for a in cursor.fetchall():
    print(a)

# ¿Tiene fines de semana asignados (FLR_ASIGNADOS)?
cursor.execute("""
    SELECT fecha_inicio, fecha_fin 
    FROM flr_asignados 
    WHERE nombre = 'Aguilera Graciela'
""")
print("\nFLR asignados a Aguilera Graciela:")
for flr in cursor.fetchall():
    print(flr)

# Ver las guardias del servicio 3 en la semana del 8 al 16 de julio (general)
print("\nGuardias en el período 2026-07-08 al 2026-07-16:")
cursor.execute("""
    SELECT fecha, turno, nombre 
    FROM guardias 
    WHERE cronograma_id = ? AND fecha BETWEEN '2026-07-08' AND '2026-07-16'
    ORDER BY fecha, turno
""", (cronograma_id,))
for g in cursor.fetchall():
    print(g)

# Ver las guardias del servicio 3 en la semana del 26 al 31 de julio
print("\nGuardias en el período 2026-07-26 al 2026-07-31:")
cursor.execute("""
    SELECT fecha, turno, nombre 
    FROM guardias 
    WHERE cronograma_id = ? AND fecha BETWEEN '2026-07-26' AND '2026-07-31'
    ORDER BY fecha, turno
""", (cronograma_id,))
for g in cursor.fetchall():
    print(g)

# Ver la demanda configurada de D_Planta y N_Planta para el servicio 3 en julio
# Para saber cuántas vacantes hay
cursor.execute("""
    SELECT tc.nombre, tc.horas, tc.dias_semana
    FROM turnos_config tc
    WHERE tc.servicio_id = 3
""")
print("\nConfiguración de Turnos Servicio 3:")
for t in cursor.fetchall():
    print(t)


conn.close()
