import sqlite3
import os

DB_PATH = "cronograma_inteligente.db"
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

SERVICIO_ID = 3

# IDs de las reglas en el catálogo
cursor.execute("SELECT id, codigo_regla FROM reglas_catalogo WHERE codigo_regla IN ('CUMPLEANOS_LIBRE', 'DIA_MADRE_PADRE_LIBRE')")
reglas = cursor.fetchall()

for regla_id, codigo in reglas:
    print(f"Activating {codigo} (ID {regla_id}) for Service {SERVICIO_ID}...")
    cursor.execute("""
        INSERT OR IGNORE INTO servicios_reglas (servicio_id, regla_id, parametros_json)
        VALUES (?, ?, ?)
    """, (SERVICIO_ID, regla_id, '{}'))

conn.commit()
conn.close()
print("Done.")
