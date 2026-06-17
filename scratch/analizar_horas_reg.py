import sqlite3

def main():
    conn = sqlite3.connect("cronograma_inteligente.db")
    cursor = conn.cursor()
    
    print("--- HORAS REGLEMENTARIAS POR SERVICIO ---")
    rows = cursor.execute("""
        SELECT servicio_id, nombre, horas_mensuales_reglamentarias
        FROM personal
        WHERE COALESCE(activo, 1) = 1
        ORDER BY servicio_id, nombre
    """).fetchall()
    
    servicios = {}
    for serv_id, nom, hs in rows:
        servicios.setdefault(serv_id, []).append((nom, hs))
        
    for serv_id, personas in servicios.items():
        print(f"\nServicio ID: {serv_id}")
        for nom, hs in personas:
            print(f"  - {nom}: {hs} hs")
            
    conn.close()

if __name__ == "__main__":
    main()
