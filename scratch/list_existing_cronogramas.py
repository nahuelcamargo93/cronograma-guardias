import sqlite3
import pandas as pd

def run():
    conn = sqlite3.connect("cronograma_inteligente.db")
    print("--- Cronogramas guardados en la BD ---")
    df_c = pd.read_sql_query("SELECT * FROM cronogramas", conn)
    print(df_c)
    
    # Veamos los servicios
    print("\n--- Servicios ---")
    df_s = pd.read_sql_query("SELECT * FROM servicios", conn)
    print(df_s)
    
    # Veamos las últimas fechas de guardias para el servicio 1 (kinesiología)
    print("\n--- Rango de guardias en BD para kinesiología ---")
    query = """
        SELECT MIN(g.fecha) as min_fecha, MAX(g.fecha) as max_fecha, COUNT(*) as cant_guardias
        FROM guardias g
        JOIN personal p ON g.nombre = p.nombre
        WHERE p.servicio_id = 1
    """
    df_g = pd.read_sql_query(query, conn)
    print(df_g)
    
    conn.close()

if __name__ == '__main__':
    run()
