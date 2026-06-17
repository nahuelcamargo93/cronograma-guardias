import sqlite3
import sys
import os

# Add workspace directory to path
sys.path.append(os.getcwd())

import main

class ConflictLogger:
    def __init__(self):
        self.lines = []
    def write(self, s):
        self.lines.append(s)
    def flush(self):
        pass

def run():
    conn = sqlite3.connect('cronograma_inteligente.db')
    print("Setting 492 to 'aprobado'...")
    conn.execute("UPDATE cronogramas SET estado = 'aprobado' WHERE id = 492")
    conn.commit()
    
    # Redirect stdout to capture print statements from reportar_conflicto
    old_stdout = sys.stdout
    logger = ConflictLogger()
    sys.stdout = logger
    
    try:
        main.ejecutar_optimizacion(
            servicio_id=3,
            fecha_inicio="2026-07-01",
            fecha_fin="2026-07-31",
            modo_debug=False,
            diagnose=True, # force assumptions
            max_time_in_seconds=10
        )
    except Exception as e:
        pass
    finally:
        sys.stdout = old_stdout
        print("Restoring 492 to 'borrador'...")
        conn.execute("UPDATE cronogramas SET estado = 'borrador' WHERE id = 492")
        conn.commit()
        conn.close()
    
    # Print the captured lines that contain the conflict rules
    output_text = "".join(logger.lines)
    print("=== CAPTURED CONFLICT RULES ===")
    in_warning = False
    for line in output_text.splitlines():
        if "[WARNING] CONFLICTO MATEMÁTICO DETECTADO" in line or "Reglas que hacen el cronograma inviable:" in line:
            in_warning = True
        if in_warning:
            if "========================" in line and len(line) > 30 and line.startswith("="):
                # End of warning block
                print(line)
                in_warning = False
            else:
                # We filter only rule names to be concise and not print thousands of lines
                if "REG_DESCANSO_ENTRE_TURNOS" in line:
                    if "hist" in line:
                        print(line)
                else:
                    print(line)

if __name__ == '__main__':
    run()
