import sqlite3

conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()

# Deactivate the conflicting fixed assignment adjustment for Mora on June 1
cursor.execute("""
    UPDATE personal_reglas_ajustes
    SET activo = 0
    WHERE personal_nombre = 'Mora, Sergio Enrique'
      AND codigo_regla = 'ASIGNACION_FIJA'
      AND fecha_inicio = '2026-06-01'
      AND fecha_fin = '2026-06-01'
""")
print(f"Updated {cursor.rowcount} row(s) in personal_reglas_ajustes.")

conn.commit()
conn.close()
