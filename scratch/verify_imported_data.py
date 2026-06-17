import sqlite3
import pandas as pd

def run():
    conn = sqlite3.connect("cronograma_inteligente.db")
    
    # 1. Comprobar cabecera del cronograma
    print("--- Verificación de Cabecera en DB ---")
    df_c = pd.read_sql_query("SELECT * FROM cronogramas WHERE id = 430", conn)
    print(df_c)
    
    # 2. Comprobar total de guardias
    print("\n--- Verificación de Guardias en DB ---")
    df_g = pd.read_sql_query("""
        SELECT COUNT(*) as cant_guardias, MIN(fecha) as min_fecha, MAX(fecha) as max_fecha
        FROM guardias
        WHERE cronograma_id = 430
    """, conn)
    print(df_g)
    
    # 3. Comprobar que no hay personas inválidas o nulas en las guardias del cronograma
    print("\n--- Verificación de Personal en Guardias ---")
    df_inv = pd.read_sql_query("""
        SELECT DISTINCT g.nombre
        FROM guardias g
        LEFT JOIN personal p ON g.nombre = p.nombre
        WHERE g.cronograma_id = 430 AND p.nombre IS NULL
    """, conn)
    if df_inv.empty:
        print("OK: Todas las personas en las guardias existen en la tabla dimensional 'personal'.")
    else:
        print("ERROR: Personas que no existen en la tabla personal:", df_inv['nombre'].tolist())
        
    # 4. Comprobar que el servicio al que pertenece el personal de las guardias del cronograma 430 es el servicio 1
    df_serv = pd.read_sql_query("""
        SELECT DISTINCT p.servicio_id
        FROM guardias g
        JOIN personal p ON g.nombre = p.nombre
        WHERE g.cronograma_id = 430
    """, conn)
    print("Servicios del personal asignado:", df_serv['servicio_id'].tolist())
    
    conn.close()

if __name__ == '__main__':
    run()
