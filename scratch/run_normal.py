import sqlite3
import subprocess

def set_crono_status(crono_id, estado):
    conn = sqlite3.connect('cronograma_inteligente.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE cronogramas SET estado = ? WHERE id = ?", (estado, crono_id))
    conn.commit()
    conn.close()

try:
    # 1. Poner crono 492 en borrador (normal)
    set_crono_status(492, 'borrador')
    
    # 2. Correr main.py normal
    print("Ejecutando main.py normal...")
    cmd = ["python", "main.py", "--servicio", "3", "--inicio", "2026-07-01", "--fin", "2026-07-31", "--timeout", "15"]
    res = subprocess.run(cmd, capture_output=True, text=True)
    print("--- STDOUT ---")
    print(res.stdout)
    print("--- STDERR ---")
    print(res.stderr)
finally:
    pass
