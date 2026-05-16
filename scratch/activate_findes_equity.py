import sqlite3
import os

os.chdir(r"c:\Users\asus\Desktop\Ryoko\cronograma_inteligente")
conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()

# Reglas de equidad de findes
reglas = [
    ('PESO_EQUIDAD_FINDES_ANUAL', '{"peso": 8000}'),
    ('PESO_EQUIDAD_FINDES_MENSUAL', '{"peso": 5000}')
]

for codigo, params in reglas:
    # Obtener ID
    cursor.execute("SELECT id FROM reglas_catalogo WHERE codigo_regla = ?", (codigo,))
    res = cursor.fetchone()
    if res:
        regla_id = res[0]
        # Insertar o actualizar para Servicio 3
        cursor.execute("DELETE FROM servicios_reglas WHERE servicio_id = 3 AND regla_id = ?", (regla_id,))
        cursor.execute("INSERT INTO servicios_reglas (servicio_id, regla_id, parametros_json) VALUES (3, ?, ?)", (regla_id, params))

conn.commit()
print("Reglas de equidad de fines de semana activadas para Médicos.")
conn.close()
