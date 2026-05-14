import sqlite3
import pandas as pd

def check_demand():
    conn = sqlite3.connect('cronograma_inteligente.db')
    query = """
        SELECT dc.tipo_dia, dc.hora_inicio, dc.hora_fin, dc.cantidad_min, dc.cantidad_max, p.nombre as puesto
        FROM demanda_config dc 
        JOIN puestos p ON dc.puesto_id = p.id 
        WHERE p.servicio_id = 2
    """
    df = pd.read_sql(query, conn)
    print(df)
    conn.close()

if __name__ == "__main__":
    check_demand()
