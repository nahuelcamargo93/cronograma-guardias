import sqlite3
import json

def main():
    conn = sqlite3.connect("cronograma_inteligente.db")
    cursor = conn.cursor()
    
    # 1. Analizar el cronograma 353
    print("--- CRONOGRAMA 353 ---")
    crono = cursor.execute("SELECT id, fecha_inicio, fecha_fin, notas, estado FROM cronogramas WHERE id = 353").fetchone()
    if crono:
        print(f"ID: {crono[0]}, Inicio: {crono[1]}, Fin: {crono[2]}, Notas: {crono[3]}, Estado: {crono[4]}")
    else:
        print("Cronograma 353 no encontrado.")
        return
        
    # 2. Infracciones registradas en infracciones_debug para 353
    print("\n--- INFRACCIONES DE REGLAS (DEBUG) EN CRONOGRAMA 353 ---")
    infracciones = cursor.execute("SELECT codigo_regla, detalle FROM infracciones_debug WHERE cronograma_id = 353").fetchall()
    for idx, (cod, det) in enumerate(infracciones):
        print(f"{idx+1}. Regla: {cod} | Detalle: {det}")
        
    # 3. Datos de personal para servicio_id = 3
    print("\n--- PERSONAL SERVICIO 3 ---")
    personal = cursor.execute("SELECT nombre, regimen_trabajo, horas_mensuales_reglamentarias FROM personal WHERE servicio_id = 3 AND COALESCE(activo, 1) = 1").fetchall()
    for nom, reg, hs in personal:
        # Sumar horas asignadas en cronograma 353 para este personal
        hs_asignadas = cursor.execute("SELECT SUM(horas) FROM guardias WHERE cronograma_id = 353 AND nombre = ?", (nom,)).fetchone()[0] or 0
        print(f"Nombre: {nom} | Regimen: {reg} | Hs Reg: {hs} | Hs Asignadas 353: {hs_asignadas}")
        
    # 4. Reglas configuradas para el servicio 3
    print("\n--- REGLAS ACTIVAS SERVICIO 3 ---")
    reglas = cursor.execute("SELECT codigo_regla, activo, parametros_json FROM servicios_reglas WHERE servicio_id = 3 AND activo = 1").fetchall()
    for cod, act, params in reglas:
        print(f"Regla: {cod} | Activa: {act} | Params: {params}")
        
    conn.close()

if __name__ == "__main__":
    main()
