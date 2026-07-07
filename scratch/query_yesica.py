import sqlite3
import json
from datetime import date, timedelta

def main():
    conn = sqlite3.connect('cronograma_inteligente.db')
    cursor = conn.cursor()
    
    crono_id = 614
    print(f"=== FERNANDEZ YESICA - CRONOGRAMA {crono_id} ===")
    
    # 1. Guardias en la semana de transición (finales de julio y 1-2 de agosto) en el cronograma 583
    print("\n--- Guardias de Yésica en Cronograma 583 (Semana de Transición 27/07 a 02/08) ---")
    guardias_trans = cursor.execute("""
        SELECT fecha, turno, horas 
        FROM guardias 
        WHERE cronograma_id = 583 AND nombre = 'FERNANDEZ YESICA' AND fecha BETWEEN '2026-07-27' AND '2026-08-02'
        ORDER BY fecha
    """).fetchall()
    for g in guardias_trans:
        print(f"Fecha: {g[0]} | Turno: {g[1]} | Horas: {g[2]}")

    # 2. Exclusiones en la semana del 3/8 al 9/8
    print("\n--- Exclusiones en Semana 3/8 a 9/8 ---")
    excl = cursor.execute("""
        SELECT fecha_inicio, fecha_fin, parametros_json 
        FROM personal_reglas_ajustes 
        WHERE personal_nombre = 'FERNANDEZ YESICA' 
          AND (fecha_inicio <= '2026-08-09' AND fecha_fin >= '2026-08-03')
          AND activo = 1
    """).fetchall()
    for ex in excl:
        print(f"Periodo: {ex[0]} a {ex[1]} | Params: {ex[2]}")

if __name__ == '__main__':
    main()
