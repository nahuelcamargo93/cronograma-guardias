import sqlite3
import json

DB_PATH = "c:/Users/asus/Desktop/Ryoko/cronograma_inteligente/cronograma_inteligente.db"
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Parámetros paramétricos finales
params = {
    "excluidos": ["POLETTI NATALIA"],
    "modo": "HARD",
    "turnos": ["MT", "TNN"],
    "cantidad": 1
}

cursor.execute("""
    UPDATE servicios_reglas 
    SET parametros_json = ?, activo = 1
    WHERE servicio_id = 2 AND codigo_regla = 'ESQUEMA_SEMANAL_ENFERMERIA'
""", (json.dumps(params),))

conn.commit()
conn.close()
print("Regla configurada paramétricamente en la BD en modo HARD para 12 hs.")
