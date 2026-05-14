import sqlite3
import json

conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()

# Actualizar peso de Objetivo Rotación Mensual a 1000
cursor.execute("SELECT sr.regla_id FROM servicios_reglas sr JOIN reglas_catalogo rc ON sr.regla_id = rc.id WHERE sr.servicio_id = 2 AND rc.codigo_regla = 'OBJETIVO_ROTACION_MENSUAL'")
row_rot = cursor.fetchone()
if row_rot:
    cursor.execute("UPDATE servicios_reglas SET parametros_json = ? WHERE servicio_id = 2 AND regla_id = ?", (json.dumps({"peso": 1000, "objetivo": 1}), row_rot[0]))
    print("Peso OBJETIVO_ROTACION_MENSUAL subido a 1000")

conn.commit()
conn.close()
