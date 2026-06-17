import sqlite3

db_path = 'cronograma_inteligente.db'

def diagnose():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("--- REGLAS ACTIVAS PARA EL SERVICIO 2 ---")
    cursor.execute("""
        SELECT codigo_regla, parametros_json
        FROM servicios_reglas
        WHERE servicio_id = 2 AND activo = 1
    """)
    for r in cursor.fetchall():
        print(r)
        
    conn.close()

if __name__ == '__main__':
    diagnose()
