import sqlite3
import os

os.chdir(r"c:\Users\asus\Desktop\Ryoko\cronograma_inteligente")
conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()

nombre = 'Murillo, Santiago'

# Limpiar ajustes previos para el mes de Junio (2026-06-01)
cursor.execute("""
    DELETE FROM personal_reglas_ajustes 
    WHERE personal_nombre = ? 
    AND codigo_regla IN ('MAX_HORAS_MES_CALENDARIO', 'MIN_HORAS_MES_CALENDARIO')
""", (nombre,))

# Insertar nuevos ajustes
params_max = '{"max_horas": 72}'
params_min = '{"min_horas": 72}'

cursor.execute("""
    INSERT INTO personal_reglas_ajustes (personal_nombre, codigo_regla, fecha_inicio, fecha_fin, accion, parametros_json)
    VALUES (?, 'MAX_HORAS_MES_CALENDARIO', '2026-06-01', '2026-06-30', 'SOBRESCRIBIR', ?)
""", (nombre, params_max))

cursor.execute("""
    INSERT INTO personal_reglas_ajustes (personal_nombre, codigo_regla, fecha_inicio, fecha_fin, accion, parametros_json)
    VALUES (?, 'MIN_HORAS_MES_CALENDARIO', '2026-06-01', '2026-06-30', 'SOBRESCRIBIR', ?)
""", (nombre, params_min))

conn.commit()
print(f"Ajuste realizado: {nombre} ahora tiene 72hs (mín/máx) para Junio.")
conn.close()
