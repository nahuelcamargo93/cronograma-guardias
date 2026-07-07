import sqlite3

conn = sqlite3.connect("cronograma_inteligente.db")
cursor = conn.cursor()

toledo_nombre = "Toledo, Andrea"
fecha_asig = "2026-08-10"
turno_asig = "Mañana_UCO"

# Eliminar asignaciones previas por fecha en ese día para Toledo para limpiar
cursor.execute("""
    DELETE FROM personal_asignaciones_fijas 
    WHERE personal_nombre = ? AND fecha = ?
""", (toledo_nombre, fecha_asig))
print(f"Eliminadas {cursor.rowcount} asignaciones fijas previas para la fecha.")

# Insertar asignación fija específica por fecha
cursor.execute("""
    INSERT INTO personal_asignaciones_fijas (personal_nombre, fecha, dia_semana, turno, activo, servicio_id)
    VALUES (?, ?, NULL, ?, 1, 1)
""", (toledo_nombre, fecha_asig, turno_asig))
print(f"Insertada asignación fija por fecha para {toledo_nombre} el {fecha_asig} con turno '{turno_asig}' (ID: {cursor.lastrowid})")

conn.commit()
conn.close()
