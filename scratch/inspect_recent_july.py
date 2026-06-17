import sqlite3

db_path = "cronograma_inteligente.db"

def inspect():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. Cronogramas con inicio en julio
    print("--- Cronogramas de Julio 2026 ---")
    cursor.execute("""
        SELECT id, fecha_inicio, fecha_fin, estado, notas 
        FROM cronogramas 
        WHERE fecha_inicio = '2026-07-01'
        ORDER BY id DESC
    """)
    rows = cursor.fetchall()
    for r in rows:
        print(f"ID: {r[0]}, Inicio: {r[1]}, Fin: {r[2]}, Estado: {r[3]}, Notas: {r[4]}")
        
        # Mostrar guardias de ABELENDA GRISELL para la semana del 29/6 al 5/7
        print(f"  Guardias de ABELENDA GRISELL (29/06 al 05/07) en Cronograma {r[0]}:")
        cursor.execute("""
            SELECT fecha, turno, horas 
            FROM guardias 
            WHERE cronograma_id = ? AND nombre LIKE '%ABELENDA%' AND fecha <= '2026-07-05'
            ORDER BY fecha
        """, [r[0]])
        guardias = cursor.fetchall()
        for g in guardias:
            print(f"    Fecha: {g[0]}, Turno: {g[1]}, Horas: {g[2]}")
            
    conn.close()

if __name__ == "__main__":
    inspect()
