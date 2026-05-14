import sqlite3
conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()
cursor.execute("SELECT sr.parametros_json FROM servicios_reglas sr JOIN reglas_catalogo rc ON sr.regla_id = rc.id WHERE sr.servicio_id = 2 AND rc.codigo_regla = 'PENALIZACION_TURNO_AUSENTE'")
row = cursor.fetchone()
print(f"Resultado DB: {row}")
conn.close()
