import sqlite3
import os

os.chdir(r"c:\Users\asus\Desktop\Ryoko\cronograma_inteligente")
conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()

names = ['Barloa Matías Damián', 'Godoy Maria']
for name in names:
    # Eliminar si ya existe algo parecido para evitar duplicados
    cursor.execute("DELETE FROM personal_reglas_ajustes WHERE personal_nombre = ? AND codigo_regla = 'MIN_HORAS_MES_CALENDARIO' AND fecha_inicio = '2026-06-01'", (name,))
    
    # Insertar suspensión
    cursor.execute("""
        INSERT INTO personal_reglas_ajustes (personal_nombre, codigo_regla, fecha_inicio, fecha_fin, accion, activo)
        VALUES (?, 'MIN_HORAS_MES_CALENDARIO', '2026-06-01', '2026-06-30', 'SUSPENDER', 1)
    """, (name,))

conn.commit()
print("Suspensión de MIN completada.")
conn.close()
