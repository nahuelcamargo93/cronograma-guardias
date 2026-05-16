import sqlite3
conn = sqlite3.connect("cronograma_inteligente.db")
conn.execute("UPDATE personal SET es_padre = 1 WHERE nombre = 'ALCARAZ FRANCISO'")
conn.commit()
conn.close()
print("Updated Alcaraz as father.")
