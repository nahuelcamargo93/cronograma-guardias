import sqlite3
import json

conn = sqlite3.connect('cronograma_inteligente.db')
c = conn.cursor()

# Get cronograma 610 info
c.execute("SELECT id, fecha_inicio, fecha_fin, creado_en, notas, estado, servicio_id FROM cronogramas WHERE id = 610")
row = c.fetchone()
print("CRONOGRAMA 610:")
print(row)

# Get count of guardias
c.execute("SELECT count(*) FROM guardias WHERE cronograma_id = 610")
print("Guardias count:", c.fetchone()[0])

# Get count of weeks in semanas_categorias
c.execute("SELECT count(*) FROM semanas_categorias WHERE cronograma_id = 610")
print("Semanas categorias count:", c.fetchone()[0])

conn.close()
