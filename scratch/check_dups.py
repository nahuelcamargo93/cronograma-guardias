import sqlite3

DB_PATH = "cronograma_inteligente.db"

def run():
    conn = sqlite3.connect(DB_PATH)
    
    print("--- Cronogramas ---")
    cursor = conn.execute("SELECT id, fecha_inicio, fecha_fin, estado FROM cronogramas WHERE estado = 'aprobado'")
    cronos = cursor.fetchall()
    for c in cronos:
        print(c)

    print("\n--- Conteo de bloques por rango de fechas ---")
    cursor = conn.execute("""
        SELECT fecha_inicio, fecha_fin, COUNT(*), GROUP_CONCAT(cronograma_id) 
        FROM bloques_finde_largo 
        GROUP BY fecha_inicio, fecha_fin
    """)
    for row in cursor.fetchall():
        print(row)
        
    print("\n--- Bloques de Finde Largo registrados ---")
    cursor = conn.execute("SELECT id, cronograma_id, fecha_inicio, fecha_fin, tipo FROM bloques_finde_largo")
    for row in cursor.fetchall():
        print(row)
        
    conn.close()

if __name__ == "__main__":
    run()
