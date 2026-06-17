import sqlite3
import subprocess

def main():
    conn = sqlite3.connect("cronograma_inteligente.db")
    cursor = conn.cursor()
    
    # 1. Guardar valores actuales de cantidad_max
    print("Guardando configuracion actual de demanda_config...")
    originales = cursor.execute("SELECT id, cantidad_max FROM demanda_config WHERE puesto_id IN (10, 11)").fetchall()
    
    # 2. Modificar cantidad_max
    print("Subiendo cantidad_max en demanda_config para el Servicio 3...")
    cursor.execute("UPDATE demanda_config SET cantidad_max = 8 WHERE puesto_id = 10") # Planta -> Max 8
    cursor.execute("UPDATE demanda_config SET cantidad_max = 5 WHERE puesto_id = 11") # Residente -> Max 5
    conn.commit()
    conn.close()
    
    # 3. Correr el optimizador en modo normal (sin debug)
    print("\nEjecutando optimizador en modo normal...")
    res = subprocess.run(["python", "main.py", "--servicio", "3", "--inicio", "2026-07-01"], capture_output=True, text=True)
    print(res.stdout)
    print(res.stderr)
    
    # 4. Restaurar valores originales
    conn = sqlite3.connect("cronograma_inteligente.db")
    cursor = conn.cursor()
    print("\nRestaurando configuracion original de demanda_config...")
    for r_id, orig_max in originales:
        cursor.execute("UPDATE demanda_config SET cantidad_max = ? WHERE id = ?", (orig_max, r_id))
    conn.commit()
    conn.close()
    
if __name__ == "__main__":
    main()
