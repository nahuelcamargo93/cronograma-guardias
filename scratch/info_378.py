import sqlite3
import os

DB_PATH = "cronograma_inteligente.db"

def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. Obtener datos del cronograma 378
    cursor.execute("SELECT id, fecha_inicio, fecha_fin, notas, estado FROM cronogramas WHERE id = 378")
    crono = cursor.fetchone()
    if not crono:
        print("No se encontró el cronograma 378")
        return
    
    print(f"Cronograma: ID={crono[0]}, Inicio={crono[1]}, Fin={crono[2]}, Notas={crono[3]}, Estado={crono[4]}")
    
    # 2. Obtener los servicios involucrados
    cursor.execute("""
        SELECT DISTINCT p.servicio_id, s.nombre 
        FROM guardias g
        JOIN personal p ON g.nombre = p.nombre
        JOIN servicios s ON p.servicio_id = s.id
        WHERE g.cronograma_id = 378
    """)
    servicios = cursor.fetchall()
    print("Servicios con guardias en cronograma 378:")
    for s in servicios:
        print(f"  ID={s[0]}, Nombre={s[1]}")
        
    # 3. Obtener el número de personas en el cronograma
    cursor.execute("SELECT DISTINCT nombre FROM guardias WHERE cronograma_id = 378")
    personas = [r[0] for r in cursor.fetchall()]
    print(f"Total personas con guardias asignadas: {len(personas)}")
    
    # 4. Obtener cantidad de registros de flr_asignados
    cursor.execute("SELECT count(*) FROM flr_asignados WHERE cronograma_id = 378")
    flr_count = cursor.fetchone()[0]
    print(f"Registros en flr_asignados: {flr_count}")

    # 5. Obtener algunos registros de flr_asignados para entender su formato
    cursor.execute("SELECT nombre, fecha_inicio, fecha_fin FROM flr_asignados WHERE cronograma_id = 378 LIMIT 5")
    flr_rows = cursor.fetchall()
    print("Muestra de flr_asignados:")
    for row in flr_rows:
        print(f"  Nombre={row[0]}, Inicio={row[1]}, Fin={row[2]}")

    conn.close()

if __name__ == "__main__":
    main()
