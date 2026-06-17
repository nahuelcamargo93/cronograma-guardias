import sqlite3
import subprocess

def main():
    conn = sqlite3.connect("cronograma_inteligente.db")
    cursor = conn.cursor()
    
    # 1. Guardar estado actual de MIN_HORAS_MES_CALENDARIO
    print("Guardando estado actual de MIN_HORAS_MES_CALENDARIO...")
    original_activo = cursor.execute("SELECT activo FROM servicios_reglas WHERE servicio_id = 3 AND codigo_regla = 'MIN_HORAS_MES_CALENDARIO'").fetchone()[0]
    
    # 2. Desactivar la regla
    print("Desactivando MIN_HORAS_MES_CALENDARIO para probar...")
    cursor.execute("UPDATE servicios_reglas SET activo = 0 WHERE servicio_id = 3 AND codigo_regla = 'MIN_HORAS_MES_CALENDARIO'")
    conn.commit()
    conn.close()
    
    # 3. Correr el optimizador en modo normal
    print("\nEjecutando optimizador sin MIN_HORAS_MES_CALENDARIO...")
    res = subprocess.run(["python", "main.py", "--servicio", "3", "--inicio", "2026-07-01"], capture_output=True, text=True)
    print(res.stdout)
    
    # 4. Restaurar estado original
    conn = sqlite3.connect("cronograma_inteligente.db")
    cursor = conn.cursor()
    print("\nRestaurando estado original de MIN_HORAS_MES_CALENDARIO...")
    cursor.execute("UPDATE servicios_reglas SET activo = ? WHERE servicio_id = 3 AND codigo_regla = 'MIN_HORAS_MES_CALENDARIO'", (original_activo,))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    main()
