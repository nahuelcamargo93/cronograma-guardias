import database.connection as c
conn = c.get_connection()
rows = conn.execute("""
    SELECT id, personal_nombre, fecha_inicio, fecha_fin, parametros_json, activo 
    FROM personal_reglas_ajustes 
    WHERE codigo_regla = 'ASIGNACION_FIJA' 
      AND fecha_inicio >= '2026-07-01' 
      AND fecha_fin <= '2026-07-31'
""").fetchall()
print("ASIGNACION_FIJA in personal_reglas_ajustes for July 2026:")
for r in rows:
    print(r)
