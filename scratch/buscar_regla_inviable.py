import sqlite3
import subprocess

def probar_configuracion(desactivar_reglas):
    conn = sqlite3.connect("cronograma_inteligente.db")
    cursor = conn.cursor()
    
    # Desactivar las reglas indicadas
    for cod in desactivar_reglas:
        cursor.execute("UPDATE servicios_reglas SET activo = 0 WHERE servicio_id = 3 AND codigo_regla = ?", (cod,))
    conn.commit()
    conn.close()
    
    # Correr optimizador
    res = subprocess.run(["python", "main.py", "--servicio", "3", "--inicio", "2026-07-01"], capture_output=True, text=True)
    
    # Restaurar
    conn = sqlite3.connect("cronograma_inteligente.db")
    cursor = conn.cursor()
    for cod in desactivar_reglas:
        cursor.execute("UPDATE servicios_reglas SET activo = 1 WHERE servicio_id = 3 AND codigo_regla = ?", (cod,))
    conn.commit()
    conn.close()
    
    return "¡CRONOGRAMA GENERADO!" in res.stdout, res.stdout

def main():
    reglas_a_probar = [
        "EXACTO_FINDE_Y_DIA",
        "DESCANSO_ENTRE_TURNOS",
        "MAX_HORAS_MES_CALENDARIO",
        "PERSONAL_DISOCIADO",
        "CUMPLEANOS_LIBRE",
        "DIA_MADRE_PADRE_LIBRE"
    ]
    
    print("--- PROBANDO DESACTIVACIÓN INDIVIDUAL ---")
    for r in reglas_a_probar:
        viable, out = probar_configuracion([r])
        print(f"Desactivando {r:<30} -> Viable: {viable}")
        if viable:
            print("  [OK] ¡Esta regla es la causante!")
            
    print("\n--- PROBANDO COMBINACIONES ---")
    # Probamos desactivar EXACTO_FINDE_Y_DIA junto con otras
    viable, out = probar_configuracion(["EXACTO_FINDE_Y_DIA", "MIN_HORAS_MES_CALENDARIO"])
    print(f"Desactivando EXACTO_FINDE_Y_DIA + MIN_HORAS_MES_CALENDARIO -> Viable: {viable}")
    
    viable, out = probar_configuracion(["DESCANSO_ENTRE_TURNOS", "MIN_HORAS_MES_CALENDARIO"])
    print(f"Desactivando DESCANSO_ENTRE_TURNOS + MIN_HORAS_MES_CALENDARIO -> Viable: {viable}")
    
    viable, out = probar_configuracion(["EXACTO_FINDE_Y_DIA", "DESCANSO_ENTRE_TURNOS"])
    print(f"Desactivando EXACTO_FINDE_Y_DIA + DESCANSO_ENTRE_TURNOS -> Viable: {viable}")
    
    viable, out = probar_configuracion(["EXACTO_FINDE_Y_DIA", "DESCANSO_ENTRE_TURNOS", "MIN_HORAS_MES_CALENDARIO"])
    print(f"Desactivando EXACTO_FINDE_Y_DIA + DESCANSO_ENTRE_TURNOS + MIN_HORAS_MES_CALENDARIO -> Viable: {viable}")

if __name__ == "__main__":
    main()
