import sqlite3

db_path = "c:/Users/asus/Desktop/Ryoko/cronograma_inteligente/cronograma_inteligente.db"
conn = sqlite3.connect(db_path)
cur = conn.cursor()

# Desactivar las reglas viejas para el servicio 2
reglas_a_desactivar = ['FINDE_LARGO_REGLAMENTARIO', 'FINDES_COMPLETOS_Y_MEDIOS']

for regla in reglas_a_desactivar:
    cur.execute("UPDATE servicios_reglas SET activo = 0 WHERE servicio_id = 2 AND codigo_regla = ?", (regla,))
    if cur.rowcount > 0:
        print(f"Regla {regla} desactivada para el servicio 2")
    else:
        print(f"La regla {regla} no estaba activa o no existía para el servicio 2")

conn.commit()
conn.close()
