import database.connection as c
conn = c.get_connection()
rows = conn.execute("""
    SELECT id, personal_nombre, fecha, dia_semana, turno, activo 
    FROM personal_asignaciones_fijas 
    WHERE servicio_id = 3 AND activo = 1
""").fetchall()
print("Active fixed assignments in personal_asignaciones_fijas:")
for r in rows:
    print(r)
