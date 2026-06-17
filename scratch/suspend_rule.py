import sqlite3
conn = sqlite3.connect('cronograma.db')
row = conn.execute("SELECT id, parametros FROM reglas_servicio WHERE servicio_id=2 AND codigo='MAX_FRANCOS_SEMANA'").fetchone()
print('Antes:', row)
if row:
    conn.execute("UPDATE reglas_servicio SET parametros=? WHERE id=?", ('{"activo": false}', row[0]))
    conn.commit()
    print('Regla suspendida')
conn.close()
