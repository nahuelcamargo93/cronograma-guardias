import sqlite3
import json

def main():
    conn = sqlite3.connect('cronograma_inteligente.db')
    cursor = conn.cursor()
    
    # 1. Definir los nuevos parámetros
    nuevos_params = {
        "peso_brecha": 5000,      # Subimos significativamente la penalización (de 100 a 5000)
        "peso_cobertura": 10
    }
    params_json = json.dumps(nuevos_params)
    
    # 2. Actualizar la base de datos
    cursor.execute("""
        UPDATE servicios_reglas 
        SET parametros_json = ? 
        WHERE servicio_id = 2 AND codigo_regla = 'PESO_BRECHA_DIARIA_PERSONAL'
    """, (params_json,))
    
    conn.commit()
    print("Base de datos actualizada con éxito.")
    
    # 3. Mostrar el valor actual para confirmar
    row = cursor.execute("""
        SELECT * FROM servicios_reglas 
        WHERE servicio_id = 2 AND codigo_regla = 'PESO_BRECHA_DIARIA_PERSONAL'
    """).fetchone()
    print("Valor actual en BD:", row)
    
    conn.close()

if __name__ == '__main__':
    main()
