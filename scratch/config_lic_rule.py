import sqlite3
import os

os.chdir(r"c:\Users\asus\Desktop\Ryoko\cronograma_inteligente")
conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()

# 1. Insertar en reglas_catalogo si no existe
cursor.execute("INSERT OR IGNORE INTO reglas_catalogo (codigo_regla, tipo, descripcion) VALUES ('CREDITO_HORARIO_LICENCIA', 'HARD', 'Define cuántas horas se acreditan por semana de licencia para el cálculo de topes.')")

# Obtener ID de la nueva regla
cursor.execute("SELECT id FROM reglas_catalogo WHERE codigo_regla = 'CREDITO_HORARIO_LICENCIA'")
regla_id = cursor.fetchone()[0]

# 2. Configurar para Servicio 3 (Médicos UTI)
cursor.execute("DELETE FROM servicios_reglas WHERE servicio_id = 3 AND regla_id = ?", (regla_id,))
cursor.execute("INSERT INTO servicios_reglas (servicio_id, regla_id, parametros_json) VALUES (3, ?, '{\"horas_por_semana\": 36}')", (regla_id,))

conn.commit()
print("Regla CREDITO_HORARIO_LICENCIA configurada para Médicos (36hs/semana).")
conn.close()
