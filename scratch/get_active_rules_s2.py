import sqlite3
import json

conn = sqlite3.connect('cronograma_inteligente.db')
c = conn.cursor()

c.execute("""
    SELECT sr.codigo_regla, rc.tipo, sr.parametros_json 
    FROM servicios_reglas sr
    JOIN reglas_catalogo rc ON sr.codigo_regla = rc.codigo_regla
    WHERE sr.servicio_id = 2 AND sr.activo = 1
""")
rows = c.fetchall()
print("ACTIVE RULES FOR SERVICE 2 IN DB:")
for r in rows:
    print(r)

conn.close()
