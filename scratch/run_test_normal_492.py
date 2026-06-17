import sys
import os
import sqlite3
import datetime

# Asegurar que el directorio raíz está en sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import main
from ortools.sat.python import cp_model
import database.queries as db_queries

def run():
    conn = sqlite3.connect('cronograma_inteligente.db')
    print("Setting 492 to 'aprobado' temporarily...")
    conn.execute("UPDATE cronogramas SET estado = 'aprobado' WHERE id = 492")
    conn.commit()
    
    try:
        servicio_id = 3
        fecha_inicio = "2026-07-01"
        fecha_fin = "2026-07-31"

        print("Executing ejecutar_optimizacion in normal mode with 492 approved...")
        res = main.ejecutar_optimizacion(
            servicio_id=servicio_id,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            notas="Test Normal",
            modo_debug=False,
            max_time_in_seconds=60,
            diagnose=False
        )
        print("RESULTADO:", res)
    finally:
        print("Restoring 492 to 'borrador'...")
        conn.execute("UPDATE cronogramas SET estado = 'borrador' WHERE id = 492")
        conn.commit()
        conn.close()

if __name__ == "__main__":
    run()
