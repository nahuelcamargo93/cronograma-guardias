import sqlite3
import pandas as pd

def main():
    conn = sqlite3.connect("cronograma_inteligente.db")
    
    print("--- Reglas individuales para personal del Servicio 4 ---")
    query = """
        SELECT pr.personal_nombre, pr.codigo_regla, pr.parametros_json, pr.activo
        FROM personal_reglas pr
        JOIN personal p ON pr.personal_nombre = p.nombre
        WHERE p.servicio_id = 4
    """
    df = pd.read_sql_query(query, conn)
    print(df.to_string())
    
    conn.close()

if __name__ == "__main__":
    main()
