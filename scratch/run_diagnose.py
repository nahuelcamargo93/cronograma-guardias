import sqlite3
import sys
import os

# Add workspace directory to path
sys.path.append(os.getcwd())

import main

def run():
    conn = sqlite3.connect('cronograma_inteligente.db')
    print("Setting 492 to 'aprobado'...")
    conn.execute("UPDATE cronogramas SET estado = 'aprobado' WHERE id = 492")
    conn.commit()
    
    try:
        print("Calling main.ejecutar_optimizacion with diagnose=True...")
        res = main.ejecutar_optimizacion(
            servicio_id=3,
            fecha_inicio="2026-07-01",
            fecha_fin="2026-07-31",
            modo_debug=False,
            diagnose=True, # force assumptions
            max_time_in_seconds=10 # limit first run to 10 seconds
        )
        print("RESULTADO:", res)
    except Exception as e:
        import traceback
        traceback.print_exc()
    finally:
        print("Restoring 492 to 'borrador'...")
        conn.execute("UPDATE cronogramas SET estado = 'borrador' WHERE id = 492")
        conn.commit()
        conn.close()

if __name__ == '__main__':
    run()
