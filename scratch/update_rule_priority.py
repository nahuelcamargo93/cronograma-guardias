import sqlite3
import json

def main():
    conn = sqlite3.connect('cronograma_inteligente.db')
    cursor = conn.cursor()
    
    print("=== ANTES ===")
    r = cursor.execute("""
        SELECT parametros_json FROM servicios_reglas 
        WHERE servicio_id = 3 AND codigo_regla = 'PENALIZACION_PUESTO_NO_PREFERIDO'
    """).fetchone()
    print(f"Parametros: {r[0] if r else 'No encontrado'}")
    
    print("\nActualizando parametros...")
    new_params = {"peso": 20000, "priorizar_categoria": "desc"}
    cursor.execute("""
        UPDATE servicios_reglas 
        SET parametros_json = ? 
        WHERE servicio_id = 3 AND codigo_regla = 'PENALIZACION_PUESTO_NO_PREFERIDO'
    """, (json.dumps(new_params),))
    conn.commit()
    
    print("\n=== DESPUES ===")
    r = cursor.execute("""
        SELECT parametros_json FROM servicios_reglas 
        WHERE servicio_id = 3 AND codigo_regla = 'PENALIZACION_PUESTO_NO_PREFERIDO'
    """).fetchone()
    print(f"Parametros: {r[0] if r else 'No encontrado'}")
    
    conn.close()

if __name__ == '__main__':
    main()
