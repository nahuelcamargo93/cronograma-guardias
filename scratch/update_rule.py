import sqlite3
import json

db_path = 'cronograma_inteligente.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Actualizar la regla MAX_FRANCOS_SEMANA para el servicio 2
nueva_config = {"limite": 3, "modo": "SOFT", "peso_soft": 10000}
nueva_config_str = json.dumps(nueva_config)

cursor.execute(
    "UPDATE servicios_reglas SET parametros_json = ? WHERE servicio_id = 2 AND codigo_regla = 'MAX_FRANCOS_SEMANA'",
    (nueva_config_str,)
)
conn.commit()

# Verificar la actualización
cursor.execute(
    "SELECT * FROM servicios_reglas WHERE servicio_id = 2 AND codigo_regla = 'MAX_FRANCOS_SEMANA'"
)
row = cursor.fetchone()
print(f"Registro actualizado: {row}")

conn.close()
