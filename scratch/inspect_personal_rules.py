import sqlite3
import pandas as pd

DB_PATH = "c:/Users/asus/Desktop/Ryoko/cronograma_inteligente/cronograma_inteligente.db"

def main():
    conn = sqlite3.connect(DB_PATH)
    
    # 1. Obtener personal
    personal = pd.read_sql_query("""
        SELECT nombre, rol, categoria, regimen_trabajo, horas_mensuales_reglamentarias 
        FROM personal 
        WHERE servicio_id = 2 AND COALESCE(activo, 1) = 1
    """, conn)
    print("=== Personal del Servicio 2 ===")
    print(personal.to_string(index=False))
    
    # 2. Obtener reglas individuales activas
    reglas = pd.read_sql_query("""
        SELECT personal_nombre, codigo_regla, parametros_json 
        FROM personal_reglas 
        WHERE activo = 1 AND personal_nombre IN (
            SELECT nombre FROM personal WHERE servicio_id = 2
        )
    """, conn)
    print("\n=== Reglas Individuales del Servicio 2 ===")
    print(reglas.to_string(index=False))
    
    conn.close()

if __name__ == '__main__':
    main()
