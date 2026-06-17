import sqlite3
import subprocess

def set_crono_status(crono_id, estado):
    conn = sqlite3.connect('cronograma_inteligente.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE cronogramas SET estado = ? WHERE id = ?", (estado, crono_id))
    conn.commit()
    conn.close()
    print(f"Crono {crono_id} seteado a {estado}.")

try:
    # 1. Poner crono 492 en aprobado
    set_crono_status(492, 'aprobado')
    
    # 2. Correr main.py con diagnose y debug-hard
    print("Ejecutando main.py...")
    # Podemos ejecutar via subprocess
    cmd = ["python", "main.py", "--servicio", "3", "--inicio", "2026-07-01", "--fin", "2026-07-31", "--diagnose"]
    res = subprocess.run(cmd, capture_output=True, text=True)
    print("--- STDOUT ---")
    print(res.stdout)
    print("--- STDERR ---")
    print(res.stderr)
finally:
    # 3. Restaurar crono 492 a borrador
    set_crono_status(492, 'borrador')
