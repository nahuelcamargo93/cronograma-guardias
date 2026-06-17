import sqlite3

def main():
    conn = sqlite3.connect("cronograma_inteligente.db")
    cursor = conn.cursor()
    
    print("--- INFRACCIONES DE REGLAS EN CRONOGRAMA 354 ---")
    infracciones = cursor.execute("SELECT codigo_regla, detalle FROM infracciones_debug WHERE cronograma_id = 354").fetchall()
    for idx, (cod, det) in enumerate(infracciones):
        print(f"{idx+1}. Regla: {cod} | Detalle: {det}")
        
    print("\n--- RESUMEN DE GUARDIAS ASIGNADAS ---")
    guardias = cursor.execute("""
        SELECT g.nombre, g.turno, COUNT(*), SUM(g.horas)
        FROM guardias g
        WHERE g.cronograma_id = 354
        GROUP BY g.nombre, g.turno
        ORDER BY g.nombre, g.turno
    """).fetchall()
    for row in guardias:
        print(f"Persona: {row[0]:<35} | Turno: {row[1]:<15} | Cantidad: {row[2]:<2} | Total Horas: {row[3]}")
        
    conn.close()

if __name__ == "__main__":
    main()
