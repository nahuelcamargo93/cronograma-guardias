import sqlite3

def main():
    conn = sqlite3.connect("cronograma_inteligente.db")
    cursor = conn.cursor()
    
    # Ver turnos_config relacionados
    turnos = cursor.execute("SELECT * FROM turnos_config WHERE puesto_id = 32").fetchall()
    print("Turnos para puesto 32:")
    for t in turnos:
        print(t)
        
    # Ver demanda_config relacionados
    demanda = cursor.execute("SELECT * FROM demanda_config WHERE puesto_id = 32").fetchall()
    print("\nDemanda config para puesto 32:")
    for d in demanda:
        print(d)
        
    # Ver demanda_ajustes relacionados
    demanda_aj = cursor.execute("""
        SELECT da.* 
        FROM demanda_ajustes da
        JOIN demanda_config dc ON da.demanda_config_id = dc.id
        WHERE dc.puesto_id = 32
    """).fetchall()
    print("\nDemanda ajustes para puesto 32:")
    for da in demanda_aj:
        print(da)
        
    conn.close()

if __name__ == "__main__":
    main()
