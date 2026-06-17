import sqlite3
import json

DB_PATH = "c:/Users/asus/Desktop/Ryoko/cronograma_inteligente/cronograma_inteligente.db"
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Actualizar parametros_json con modo SOFT y excluidos
params = {
    "excluidos": ["POLETTI NATALIA"],
    "modo": "SOFT",
    "peso_soft": 10000
}

cursor.execute("""
    UPDATE servicios_reglas 
    SET parametros_json = ?, activo = 1
    WHERE servicio_id = 2 AND codigo_regla = 'ESQUEMA_SEMANAL_ENFERMERIA'
""", (json.dumps(params),))

conn.commit()
conn.close()
print("Parámetros actualizados a modo SOFT en la base de datos.")
