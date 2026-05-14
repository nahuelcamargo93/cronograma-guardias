import sqlite3
import json

def switch_flr_rules():
    conn = sqlite3.connect('cronograma_inteligente.db')
    cursor = conn.cursor()
    
    # 1. Desactivar FINDE_LARGO_REGLAMENTARIO (si existe)
    cursor.execute("SELECT valor FROM reglas_servicio WHERE servicio_id = 2 AND nombre = 'FINDE_LARGO_REGLAMENTARIO'")
    row = cursor.fetchone()
    if row:
        val = json.loads(row[0])
        val['suspendida'] = True
        cursor.execute("UPDATE reglas_servicio SET valor = ? WHERE servicio_id = 2 AND nombre = 'FINDE_LARGO_REGLAMENTARIO'", (json.dumps(val),))
    else:
        # Si no existe, creamos una suspendida por las dudas
        cursor.execute("INSERT INTO reglas_servicio (servicio_id, nombre, valor) VALUES (?, ?, ?)", 
                       (2, 'FINDE_LARGO_REGLAMENTARIO', json.dumps({'suspendida': True})))

    # 2. Activar FINDE_LARGO_REGLAMENTARIO_ESTRICTO
    cursor.execute("SELECT valor FROM reglas_servicio WHERE servicio_id = 2 AND nombre = 'FINDE_LARGO_REGLAMENTARIO_ESTRICTO'")
    row = cursor.fetchone()
    if row:
        val = json.loads(row[0])
        val['suspendida'] = False
        val['cantidad'] = 1
        cursor.execute("UPDATE reglas_servicio SET valor = ? WHERE servicio_id = 2 AND nombre = 'FINDE_LARGO_REGLAMENTARIO_ESTRICTO'", (json.dumps(val),))
    else:
        cursor.execute("INSERT INTO reglas_servicio (servicio_id, nombre, valor) VALUES (?, ?, ?)", 
                       (2, 'FINDE_LARGO_REGLAMENTARIO_ESTRICTO', json.dumps({'suspendida': False, 'cantidad': 1})))
    
    conn.commit()
    conn.close()
    print("Reglas de FLR actualizadas: NORMAL (suspendida) | ESTRICTA (activa)")

if __name__ == "__main__":
    switch_flr_rules()
