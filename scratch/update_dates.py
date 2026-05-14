import sqlite3
import os

os.chdir(r"c:\Users\asus\Desktop\Ryoko\cronograma_inteligente")
conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()

# Actualizar fecha_inicio para todos los ajustes de personal del servicio 3
cursor.execute("""
    UPDATE personal_reglas_ajustes 
    SET fecha_inicio = '2026-06-01' 
    WHERE personal_nombre IN (SELECT nombre FROM personal WHERE servicio_id = 3)
""")

# También asegurar que la fecha_fin sea después de la fecha_inicio si por error quedó antes
cursor.execute("""
    UPDATE personal_reglas_ajustes 
    SET fecha_fin = '2026-06-30' 
    WHERE personal_nombre IN (SELECT nombre FROM personal WHERE servicio_id = 3)
    AND fecha_fin < '2026-06-01'
""")

conn.commit()
print(f"Actualizados {cursor.rowcount} registros.")
conn.close()
