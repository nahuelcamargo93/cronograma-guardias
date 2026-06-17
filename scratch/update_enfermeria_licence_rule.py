import sqlite3
import json

def update_db():
    conn = sqlite3.connect('cronograma_inteligente.db')
    cursor = conn.cursor()
    
    # Ver los valores antes
    cursor.execute("""
        SELECT id, codigo_regla, parametros_json, activo 
        FROM servicios_reglas 
        WHERE servicio_id = 2 AND codigo_regla = 'CREDITO_HORARIO_LICENCIA';
    """)
    row = cursor.fetchone()
    if row:
        print(f"Valores previos: ID {row[0]} | Codigo {row[1]} | Activo {row[3]} | Params {row[2]}")
        
        # Actualizar
        new_params = {"horas_mensuales_base": 144}
        cursor.execute("""
            UPDATE servicios_reglas 
            SET parametros_json = ? 
            WHERE servicio_id = 2 AND codigo_regla = 'CREDITO_HORARIO_LICENCIA';
        """, (json.dumps(new_params),))
        conn.commit()
        print("Regla actualizada exitosamente.")
        
        # Ver los valores despues
        cursor.execute("""
            SELECT id, codigo_regla, parametros_json, activo 
            FROM servicios_reglas 
            WHERE servicio_id = 2 AND codigo_regla = 'CREDITO_HORARIO_LICENCIA';
        """)
        row_new = cursor.fetchone()
        print(f"Valores nuevos: ID {row_new[0]} | Codigo {row_new[1]} | Activo {row_new[3]} | Params {row_new[2]}")
    else:
        print("No se encontro la regla CREDITO_HORARIO_LICENCIA para el servicio_id = 2.")
        
    conn.close()

if __name__ == "__main__":
    update_db()
