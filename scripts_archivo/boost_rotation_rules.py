import sqlite3
import json

conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()

# 1. Subir penalización por turno ausente
cursor.execute("SELECT sr.regla_id FROM servicios_reglas sr JOIN reglas_catalogo rc ON sr.regla_id = rc.id WHERE sr.servicio_id = 2 AND rc.codigo_regla = 'PENALIZACION_TURNO_AUSENTE'")
row_div = cursor.fetchone()
if row_div:
    cursor.execute("UPDATE servicios_reglas SET parametros_json = ? WHERE servicio_id = 2 AND regla_id = ?", (json.dumps({"peso": 5000}), row_div[0]))
    print("Peso PENALIZACION_TURNO_AUSENTE subido a 5000")

# 2. Subir peso de Objetivo Rotación Mensual
cursor.execute("SELECT sr.regla_id FROM servicios_reglas sr JOIN reglas_catalogo rc ON sr.regla_id = rc.id WHERE sr.servicio_id = 2 AND rc.codigo_regla = 'OBJETIVO_ROTACION_MENSUAL'")
row_rot = cursor.fetchone()
if row_rot:
    cursor.execute("UPDATE servicios_reglas SET parametros_json = ? WHERE servicio_id = 2 AND regla_id = ?", (json.dumps({"peso": 500, "objetivo": 1}), row_rot[0]))
    print("Peso OBJETIVO_ROTACION_MENSUAL subido a 500")

conn.commit()
conn.close()
