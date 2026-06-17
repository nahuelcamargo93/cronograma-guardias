import sqlite3

conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()

# Ver los empleados del servicio 1
print("=== Personal del Servicio 1 ===")
cursor.execute("SELECT nombre, categoria, rol, regimen_trabajo, horas_mensuales_reglamentarias FROM personal WHERE servicio_id = 1")
for row in cursor.fetchall():
    print(f"Nombre: {row[0]} | Cat: {row[1]} | Rol: {row[2]} | Regimen: {row[3]} | Horas: {row[4]}")

# Ver si ya existen reglas aplicadas en personal_reglas para estos empleados
print("\n=== Reglas actuales en personal_reglas para Servicio 1 ===")
cursor.execute("""
    SELECT r.personal_nombre, r.codigo_regla, r.parametros_json, r.activo 
    FROM personal_reglas r
    JOIN personal p ON r.personal_nombre = p.nombre
    WHERE p.servicio_id = 1
""")
for row in cursor.fetchall():
    print(f"Empleado: {row[0]} | Regla: {row[1]} | Params: {row[2]} | Activo: {row[3]}")

conn.close()
