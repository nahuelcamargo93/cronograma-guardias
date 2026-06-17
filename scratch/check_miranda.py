import sqlite3

db_path = "cronograma_inteligente.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

crono_id = 258

def check_empleado(name, semana_inicio_str, semana_fin_str, ult_crono_id=128):
    print(f"\n==========================================")
    print(f"EMPLEADO: {name} (Semana: {semana_inicio_str})")
    print(f"==========================================")
    
    # Historial (si aplica para la primera semana)
    cursor.execute("""
        SELECT fecha, turno, horas 
        FROM guardias 
        WHERE cronograma_id = ? AND nombre = ? AND fecha >= ? AND fecha <= ?
    """, (ult_crono_id, name, semana_inicio_str, '2026-06-30'))
    hist = cursor.fetchall()
    if hist:
        print("--- Historial (Junio) ---")
        for r in hist:
            print(r)
            
    # Asignaciones actuales (Julio)
    cursor.execute("""
        SELECT fecha, turno, horas 
        FROM guardias 
        WHERE cronograma_id = ? AND nombre = ? AND fecha >= ? AND fecha <= ?
    """, (crono_id, name, semana_inicio_str, semana_fin_str))
    print("--- Asignaciones (Julio) ---")
    for r in cursor.fetchall():
        print(r)

check_empleado("MIRANDA YANINA", "2026-06-29", "2026-07-05")
check_empleado("GOMES STHEFANIA", "2026-07-20", "2026-07-26")

conn.close()
