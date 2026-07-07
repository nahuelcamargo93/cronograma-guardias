import sqlite3

def main():
    conn = sqlite3.connect('cronograma_inteligente.db')
    cursor = conn.cursor()
    
    print("--- Updating MANEJO_FINDES to peso_soft=10000000 for servicio_id=2 ---")
    nuevo_json = '{"modo": "SOFT", "peso_soft": 10000000, "por_disponibilidad": {"5": {"flr": 1, "completos": 3, "medios": 1}, "4": {"flr": 1, "completos": 2, "medios": 1}, "3": {"flr": 0, "completos": 1, "medios": 1}, "2": {"flr": 0, "completos": 2, "medios": 0}, "1": {"flr": 0, "completos": 1, "medios": 0}}, "flr_permitidos": ["sm", "vl", "jd"]}'
    cursor.execute("UPDATE servicios_reglas SET parametros_json=? WHERE servicio_id=2 AND codigo_regla='MANEJO_FINDES'", (nuevo_json,))
    conn.commit()
    print("Update completed successfully.")

if __name__ == '__main__':
    main()
