import sqlite3
conn = sqlite3.connect('cronograma_inteligente.db')
conn.execute('UPDATE personal SET fecha_cumpleanos = "1985-05-25" WHERE nombre = "ALCARAZ FRANCISO"')
conn.commit()
conn.close()
print("Manual fix done.")
