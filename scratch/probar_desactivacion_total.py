import sqlite3
import subprocess

def main():
    conn = sqlite3.connect("cronograma_inteligente.db")
    cursor = conn.cursor()
    
    # 1. Guardar estado de todas las reglas EXACTO_FINDE_Y_DIA y MIN_HORAS_MES_CALENDARIO
    print("Guardando configuracion actual de EXACTO_FINDE_Y_DIA y MIN_HORAS_MES_CALENDARIO...")
    sr_originales = cursor.execute("SELECT codigo_regla, activo FROM servicios_reglas WHERE servicio_id = 3").fetchall()
    pr_originales = cursor.execute("SELECT id, activo FROM personal_reglas").fetchall()
    pra_originales = cursor.execute("SELECT id, activo FROM personal_reglas_ajustes").fetchall()
    
    # 2. Desactivar en todos los niveles
    print("Desactivando EXACTO_FINDE_Y_DIA y MIN_HORAS_MES_CALENDARIO en todos los niveles...")
    cursor.execute("UPDATE servicios_reglas SET activo = 0 WHERE servicio_id = 3 AND codigo_regla IN ('EXACTO_FINDE_Y_DIA', 'MIN_HORAS_MES_CALENDARIO')")
    cursor.execute("UPDATE personal_reglas SET activo = 0 WHERE codigo_regla IN ('EXACTO_FINDE_Y_DIA', 'MIN_HORAS_MES_CALENDARIO')")
    cursor.execute("UPDATE personal_reglas_ajustes SET activo = 0 WHERE codigo_regla IN ('EXACTO_FINDE_Y_DIA', 'MIN_HORAS_MES_CALENDARIO')")
    conn.commit()
    conn.close()
    
    # 3. Correr el optimizador
    print("\nEjecutando optimizador en modo normal...")
    res = subprocess.run(["python", "main.py", "--servicio", "3", "--inicio", "2026-07-01"], capture_output=True, text=True)
    print(res.stdout)
    
    # 4. Restaurar todo
    conn = sqlite3.connect("cronograma_inteligente.db")
    cursor = conn.cursor()
    print("\nRestaurando configuraciones originales...")
    for cod, act in sr_originales:
        cursor.execute("UPDATE servicios_reglas SET activo = ? WHERE servicio_id = 3 AND codigo_regla = ?", (act, cod))
    for r_id, act in pr_originales:
        cursor.execute("UPDATE personal_reglas SET activo = ? WHERE id = ?", (act, r_id))
    for r_id, act in pra_originales:
        cursor.execute("UPDATE personal_reglas_ajustes SET activo = ? WHERE id = ?", (act, r_id))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    main()
