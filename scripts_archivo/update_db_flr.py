import sqlite3
import json

def update_flr_rules():
    conn = sqlite3.connect('cronograma_inteligente.db')
    cursor = conn.cursor()
    
    # Obtener IDs de las reglas
    cursor.execute("SELECT id FROM reglas_catalogo WHERE codigo_regla = 'FINDE_LARGO_REGLAMENTARIO'")
    id_normal = cursor.fetchone()
    
    cursor.execute("SELECT id FROM reglas_catalogo WHERE codigo_regla = 'FINDE_LARGO_REGLAMENTARIO_ESTRICTO'")
    id_estricto = cursor.fetchone()
    
    # Si no existe la estricta en el catalogo, la creamos
    if not id_estricto:
        cursor.execute("INSERT INTO reglas_catalogo (codigo_regla, tipo, descripcion) VALUES (?, ?, ?)",
                       ('FINDE_LARGO_REGLAMENTARIO_ESTRICTO', 'SOFT', 'Finde largo obligatorio que debe caer dentro del mes'))
        id_estricto = (cursor.lastrowid,)

    # 1. Suspender la normal para el servicio 2
    if id_normal:
        cursor.execute("SELECT parametros_json FROM servicios_reglas WHERE servicio_id = 2 AND regla_id = ?", id_normal)
        row = cursor.fetchone()
        if row:
            params = json.loads(row[0])
            params['suspendida'] = True
            cursor.execute("UPDATE servicios_reglas SET parametros_json = ? WHERE servicio_id = 2 AND regla_id = ?", (json.dumps(params), id_normal[0]))
    
    # 2. Activar la estricta para el servicio 2
    cursor.execute("SELECT parametros_json FROM servicios_reglas WHERE servicio_id = 2 AND regla_id = ?", id_estricto)
    row = cursor.fetchone()
    if row:
        params = json.loads(row[0])
        params['suspendida'] = False
        params['cantidad'] = 1
        cursor.execute("UPDATE servicios_reglas SET parametros_json = ? WHERE servicio_id = 2 AND regla_id = ?", (json.dumps(params), id_estricto[0]))
    else:
        cursor.execute("INSERT INTO servicios_reglas (servicio_id, regla_id, parametros_json) VALUES (?, ?, ?)",
                       (2, id_estricto[0], json.dumps({'suspendida': False, 'cantidad': 1})))
    
    conn.commit()
    conn.close()
    print("Reglas actualizadas correctamente en la base de datos.")

if __name__ == "__main__":
    update_flr_rules()
