import sqlite3
conn = sqlite3.connect(r'c:\Users\asus\Desktop\Ryoko\cronograma_inteligente\cronograma_inteligente.db')
res = conn.execute("SELECT parametros_json FROM servicios_reglas s JOIN reglas_catalogo r ON s.regla_id = r.id WHERE s.servicio_id = 3 AND r.codigo_regla = 'MIN_HORAS_MES_CALENDARIO'").fetchone()
print(res)
