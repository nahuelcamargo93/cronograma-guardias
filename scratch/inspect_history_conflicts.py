import sqlite3
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import queries as db_queries
from data import FECHA_INICIO, SERVICIO_ID

def inspect():
    historial = db_queries.cargar_guardias_previas(FECHA_INICIO, dias_atras=28, servicio_id=SERVICIO_ID)
    print("=== PRIOR GUARDIAS (END OF MAY 2026) ===")
    
    # Let's check for any guards in the last week of May (2026-05-25 to 2026-05-31)
    for emp_name, guards in historial.items():
        # filter Category A employees
        conn = sqlite3.connect("cronograma_inteligente.db")
        cat = conn.execute("SELECT categoria, rol FROM personal WHERE nombre = ?", (emp_name,)).fetchone()
        conn.close()
        
        if cat and cat[0] == 'A':
            recent_guards = [g for g in guards if g['fecha'] >= '2026-05-25']
            if recent_guards:
                print(f"\nEmployee: {emp_name} (Cat: {cat[0]}, Rol: {cat[1]})")
                for g in recent_guards:
                    print(f"  Fecha: {g['fecha']} | Turno: {g['turno']} | Horas: {g['horas']}")

if __name__ == "__main__":
    inspect()
