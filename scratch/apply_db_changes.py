import sqlite3
import json

def main():
    conn = sqlite3.connect('cronograma_inteligente.db')
    cursor = conn.cursor()

    # 1. Cambiar el modo de la regla EXACTO_FINDE_Y_DIA a SOFT en servicios_reglas para Servicio 3
    cursor.execute("""
        SELECT parametros_json
        FROM servicios_reglas
        WHERE servicio_id = 3 AND codigo_regla = 'EXACTO_FINDE_Y_DIA'
    """)
    row = cursor.fetchone()
    if row:
        params = json.loads(row[0])
        params['modo'] = 'SOFT'
        cursor.execute("""
            UPDATE servicios_reglas
            SET parametros_json = ?
            WHERE servicio_id = 3 AND codigo_regla = 'EXACTO_FINDE_Y_DIA'
        """, (json.dumps(params),))
        print("Modo de EXACTO_FINDE_Y_DIA en servicios_reglas actualizado a SOFT.")
    else:
        print("ERROR: No se encontró la regla EXACTO_FINDE_Y_DIA para Servicio 3 en servicios_reglas.")

    # 2. Agregar la suspensión en personal_reglas para Barloa, Godoy y Quintero
    nombres = ['Barloa Matías Damián', 'Godoy Maria', 'Quintero Anabela Belen']
    suspension_params = json.dumps({"suspendida": True})
    
    for nom in nombres:
        cursor.execute("""
            INSERT OR REPLACE INTO personal_reglas (personal_nombre, codigo_regla, parametros_json, activo)
            VALUES (?, 'EXACTO_FINDE_Y_DIA', ?, 1)
        """, (nom, suspension_params))
        print(f"Suspensión de EXACTO_FINDE_Y_DIA agregada para {nom} en personal_reglas.")

    conn.commit()
    conn.close()
    print("Base de datos actualizada correctamente.")

if __name__ == '__main__':
    main()
