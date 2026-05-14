import sqlite3
import pandas as pd
import json

def setup_workload_limits():
    conn = sqlite3.connect('cronograma_inteligente.db')
    cursor = conn.cursor()
    
    SERVICIO_ID = 3
    FECHA_INI = "2026-07-01"
    FECHA_FIN = "2026-07-31"
    
    print(f"--- Setting up Workload Limits for Service {SERVICIO_ID} ---")
    
    # 1. Service-level defaults
    # Rule 169: MIN_HORAS_MES_CALENDARIO
    cursor.execute("DELETE FROM servicios_reglas WHERE servicio_id = ? AND regla_id = 169", (SERVICIO_ID,))
    cursor.execute("INSERT INTO servicios_reglas (servicio_id, regla_id, parametros_json) VALUES (?, ?, ?)",
                   (SERVICIO_ID, 169, json.dumps({"min_horas": 144})))
    
    # Rule 140: MAX_HORAS_MES_CALENDARIO
    cursor.execute("DELETE FROM servicios_reglas WHERE servicio_id = ? AND regla_id = 140", (SERVICIO_ID,))
    cursor.execute("INSERT INTO servicios_reglas (servicio_id, regla_id, parametros_json) VALUES (?, ?, ?)",
                   (SERVICIO_ID, 140, json.dumps({"max_horas": 192})))
    
    # Rule 114: LIMITES_SOFT_RULES (Required for scaling)
    cursor.execute("DELETE FROM servicios_reglas WHERE servicio_id = ? AND regla_id = 114", (SERVICIO_ID,))
    cursor.execute("INSERT INTO servicios_reglas (servicio_id, regla_id, parametros_json) VALUES (?, ?, ?)",
                   (SERVICIO_ID, 114, json.dumps({
                       "SEMANAS_BASE": 4, 
                       "MIN_HORAS_BASE": 144, 
                       "MAX_HORAS_LIMITE_BASE": 192, 
                       "MAX_ANUAL_LIMITE": 5000, 
                       "MAX_SEG_LIMITE_BASE": 50, 
                       "MAX_FINDES_LIMITE_BASE": 8
                   })))
    
    print("Service-level defaults set: Min 144, Max 192.")
    
    # 2. Individual Adjustments
    print("\n--- Processing Individual Overrides from Excel ---")
    df = pd.read_excel('Personal medico (con LAR y LPP).xlsx')
    
    # Clear previous adjustments for these rules in this period to avoid duplicates
    cursor.execute("""
        DELETE FROM personal_reglas_ajustes 
        WHERE (codigo_regla = 'MIN_HORAS_MES_CALENDARIO' OR codigo_regla = 'MAX_HORAS_MES_CALENDARIO')
        AND fecha_inicio = ? AND fecha_fin = ?
    """, (FECHA_INI, FECHA_FIN))
    
    count_min = 0
    count_max = 0
    
    for idx, row in df.iterrows():
        nombre = str(row['Nombre']).strip()
        if nombre == "nan" or not nombre:
            continue
            
        min_h = row['Horas Mensuales']
        max_h = row['Horas posibles TOTALES']
        
        # Override Min if not 144
        if not pd.isna(min_h) and min_h != 144:
            cursor.execute("""
                INSERT INTO personal_reglas_ajustes (personal_nombre, codigo_regla, fecha_inicio, fecha_fin, accion, parametros_json, activo)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (nombre, 'MIN_HORAS_MES_CALENDARIO', FECHA_INI, FECHA_FIN, 'SOBRESCRIBIR', json.dumps({"min_horas": int(min_h)}), 1))
            count_min += 1
            
        # Override Max if not 192
        if not pd.isna(max_h) and max_h != 192:
            cursor.execute("""
                INSERT INTO personal_reglas_ajustes (personal_nombre, codigo_regla, fecha_inicio, fecha_fin, accion, parametros_json, activo)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (nombre, 'MAX_HORAS_MES_CALENDARIO', FECHA_INI, FECHA_FIN, 'SOBRESCRIBIR', json.dumps({"max_horas": int(max_h)}), 1))
            count_max += 1
            
    print(f"Applied {count_min} overrides for Min Hours.")
    print(f"Applied {count_max} overrides for Max Hours.")
    
    conn.commit()
    conn.close()
    print("\n--- Workload Setup Finished ---")

if __name__ == "__main__":
    setup_workload_limits()
