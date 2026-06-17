import sqlite3
import json

DB_PATH = "c:/Users/asus/Desktop/Ryoko/cronograma_inteligente/cronograma_inteligente.db"
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Configurar ESQUEMA_SEMANAL_ENFERMERIA en modo SOFT con peso alto (50000)
params = {
    "excluidos": ["POLETTI NATALIA"],
    "modo": "SOFT",
    "peso_soft": 50000
}

cursor.execute("""
    UPDATE servicios_reglas 
    SET parametros_json = ?, activo = 1
    WHERE servicio_id = 2 AND codigo_regla = 'ESQUEMA_SEMANAL_ENFERMERIA'
""", (json.dumps(params),))

conn.commit()
conn.close()
print("Regla configurada en modo SOFT con peso 50000.")
