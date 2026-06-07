import sqlite3
import json

def switch_flr_rules():
    conn = sqlite3.connect('cronograma_inteligente.db')
    cursor = conn.cursor()
    
    # 1. Desactivar FINDE_LARGO_REGLAMENTARIO para el servicio 2
    cursor.execute("SELECT parametros_json FROM servicios_reglas WHERE servicio_id = 2 AND codigo_regla = 'FINDE_LARGO_REGLAMENTARIO'")
    row = cursor.fetchone()
    if row:
        val = json.loads(row[0])
        val['suspendida'] = True
        cursor.execute("UPDATE servicios_reglas SET parametros_json = ?, activo = 0 WHERE servicio_id = 2 AND codigo_regla = 'FINDE_LARGO_REGLAMENTARIO'", (json.dumps(val),))
    else:
        cursor.execute("INSERT INTO servicios_reglas (servicio_id, codigo_regla, parametros_json, activo) VALUES (?, ?, ?, ?)", 
                       (2, 'FINDE_LARGO_REGLAMENTARIO', json.dumps({'suspendida': True}), 0))

    # 2. Activar FINDE_LARGO_REGLAMENTARIO_ESTRICTO para el servicio 2
    cursor.execute("SELECT parametros_json FROM servicios_reglas WHERE servicio_id = 2 AND codigo_regla = 'FINDE_LARGO_REGLAMENTARIO_ESTRICTO'")
    row = cursor.fetchone()
    if row:
        val = json.loads(row[0])
        val['suspendida'] = False
        val['cantidad'] = 1
        val['modo'] = 'HARD'
        cursor.execute("UPDATE servicios_reglas SET parametros_json = ?, activo = 1 WHERE servicio_id = 2 AND codigo_regla = 'FINDE_LARGO_REGLAMENTARIO_ESTRICTO'", (json.dumps(val),))
    else:
        cursor.execute("INSERT INTO servicios_reglas (servicio_id, codigo_regla, parametros_json, activo) VALUES (?, ?, ?, ?)", 
                       (2, 'FINDE_LARGO_REGLAMENTARIO_ESTRICTO', json.dumps({'suspendida': False, 'cantidad': 1, 'modo': 'HARD'}), 1))
    
    conn.commit()
    conn.close()
    print("Reglas de FLR actualizadas: NORMAL (suspendida) | ESTRICTA (activa/HARD)")

if __name__ == "__main__":
    switch_flr_rules()
