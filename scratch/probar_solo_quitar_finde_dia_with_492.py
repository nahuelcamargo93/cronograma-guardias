import sqlite3
import subprocess
import os
import sys

def main():
    conn = sqlite3.connect("cronograma_inteligente.db")
    cursor = conn.cursor()
    
    print("Setting 492 to approved...")
    cursor.execute("UPDATE cronogramas SET estado = 'aprobado' WHERE id = 492")
    conn.commit()

    # Save state of rules
    print("Guardando configuracion actual de EXACTO_FINDE_Y_DIA...")
    sr_originales = cursor.execute("SELECT codigo_regla, activo FROM servicios_reglas WHERE servicio_id = 3").fetchall()
    
    # Desactivar EXACTO_FINDE_Y_DIA in servicios_reglas
    print("Desactivando EXACTO_FINDE_Y_DIA...")
    cursor.execute("UPDATE servicios_reglas SET activo = 0 WHERE servicio_id = 3 AND codigo_regla = 'EXACTO_FINDE_Y_DIA'")
    conn.commit()
    conn.close()
    
    try:
        # Correr el optimizador
        print("\nEjecutando optimizador en modo normal con 492 aprobado...")
        res = subprocess.run(["python", "main.py", "--servicio", "3", "--inicio", "2026-07-01"], capture_output=True, text=True)
        print("STDOUT:")
        print(res.stdout)
        print("STDERR:")
        print(res.stderr)
    finally:
        # Restaurar todo
        conn = sqlite3.connect("cronograma_inteligente.db")
        cursor = conn.cursor()
        print("\nRestaurando configuraciones originales...")
        for cod, act in sr_originales:
            cursor.execute("UPDATE servicios_reglas SET activo = ? WHERE servicio_id = 3 AND codigo_regla = ?", (act, cod))
        cursor.execute("UPDATE cronogramas SET estado = 'borrador' WHERE id = 492")
        conn.commit()
        conn.close()

if __name__ == "__main__":
    main()
