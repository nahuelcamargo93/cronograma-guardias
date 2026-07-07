import sqlite3

def inspect():
    conn = sqlite3.connect("cronograma_inteligente.db")
    cursor = conn.cursor()
    
    print("--- EMPLEADOS CON 'Moya' ---")
    cursor.execute("SELECT nombre, servicio_id, activo, rol FROM personal WHERE nombre LIKE '%Moya%'")
    for row in cursor.fetchall():
        print(row)
        
    print("\n--- TURNOS CONFIGURADOS PARA SERVICIO 3 ---")
    cursor.execute("SELECT nombre, sigla, horas, dias_semana, activo FROM turnos_config WHERE servicio_id = 3")
    for row in cursor.fetchall():
        print(row)
        
    print("\n--- REGLAS ASOCIADAS A MOYA (u homónimo) ---")
    cursor.execute("""
        SELECT personal_nombre, codigo_regla, parametros_json, activo, servicio_id 
        FROM personal_reglas 
        WHERE personal_nombre LIKE '%Moya%'
    """)
    for row in cursor.fetchall():
        print(row)
        
    conn.close()

if __name__ == "__main__":
    inspect()
