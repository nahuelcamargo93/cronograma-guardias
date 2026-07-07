import sqlite3
import json

conn = sqlite3.connect("cronograma_inteligente.db")
cursor = conn.cursor()

# 1. Buscar nombres exactos de Toledo y García en el servicio 1
print("=== Buscando personal ===")
cursor.execute("SELECT nombre, rol FROM personal WHERE servicio_id = 1 AND (nombre LIKE '%TOLEDO%' OR nombre LIKE '%GARCIA%')")
for r in cursor.fetchall():
    print(r)

# Guardar nombres exactos de Toledo y García (asumiendo coincidencia)
# Vamos a buscarlos programáticamente en la BD
cursor.execute("SELECT nombre FROM personal WHERE servicio_id = 1 AND nombre LIKE '%TOLEDO%'")
toledo_row = cursor.fetchone()
toledo_nombre = toledo_row[0] if toledo_row else "TOLEDO ANDREA"

cursor.execute("SELECT nombre FROM personal WHERE servicio_id = 1 AND nombre LIKE '%GARCIA%'")
garcia_row = cursor.fetchone()
garcia_nombre = garcia_row[0] if garcia_row else "GARCIA LUCIANO"

print(f"Nombres exactos identificados: '{toledo_nombre}' y '{garcia_nombre}'")

# 2. Eliminar cualquier franco forzado previo de agosto para ellos para limpiar la prueba
cursor.execute("""
    DELETE FROM personal_reglas_ajustes 
    WHERE servicio_id = 1 
      AND personal_nombre IN (?, ?) 
      AND codigo_regla = 'FRANCO_FORZADO'
      AND fecha_inicio LIKE '2026-08-%'
""", (toledo_nombre, garcia_nombre))
print(f"Eliminados {cursor.rowcount} francos forzados de prueba previos en agosto.")

# 3. Insertar nuevos francos forzados
# Toledo Andrea: 8 al 11 de agosto (2026-08-08 al 2026-08-11)
# García Luciano: 14 al 17 de agosto (2026-08-14 al 2026-08-17)
adjustments = [
    (toledo_nombre, "FRANCO_FORZADO", "2026-08-08", "2026-08-11", "SOBRESCRIBIR", "{}", 1, 1),
    (garcia_nombre, "FRANCO_FORZADO", "2026-08-14", "2026-08-17", "SOBRESCRIBIR", "{}", 1, 1),
]

print("\n=== Insertando FRANCO_FORZADO de prueba ===")
for row in adjustments:
    cursor.execute("""
        INSERT INTO personal_reglas_ajustes (personal_nombre, codigo_regla, fecha_inicio, fecha_fin, accion, parametros_json, activo, servicio_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, row)
    print(f"Insertado FRANCO_FORZADO para {row[0]} del {row[2]} al {row[3]} (ID: {cursor.lastrowid})")

conn.commit()

# 4. Inspeccionar asignaciones fijas activas para ellos
print("\n=== Inspeccionando ASIGNACIONES FIJAS base ===")
cursor.execute("""
    SELECT pr.personal_nombre, pr.parametros_json 
    FROM personal_reglas pr
    INNER JOIN reglas_catalogo rc ON pr.regla_id = rc.id
    WHERE rc.codigo_regla = 'ASIGNACION_FIJA'
      AND pr.personal_nombre IN (?, ?)
""", (toledo_nombre, garcia_nombre))
for r in cursor.fetchall():
    print(f"Nombre: {r[0]}")
    print(f"JSON: {r[1]}")

conn.close()
print("\nFinalizado.")
