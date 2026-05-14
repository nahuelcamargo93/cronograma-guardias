import sqlite3
import json

def apply_more_adjustments():
    conn = sqlite3.connect('cronograma_inteligente.db')
    cursor = conn.cursor()
    
    fecha_inicio = '2026-05-01'
    fecha_fin = '2026-12-31'
    rule_code = 'EXCLUIR_TURNOS'
    
    # Group 1: Tuesdays (Martes=1)
    group1 = ['DURAN JAZMIN', 'SOSA NAHUEL', 'CASTRO LUCIANO']
    params1 = json.dumps([{"turnos": ["N", "M", "MT"], "dias": [1]}])
    
    for name in group1:
        print(f"Applying adjustment for {name} (Tuesdays)...")
        cursor.execute("""
            INSERT INTO personal_reglas_ajustes (personal_nombre, codigo_regla, fecha_inicio, fecha_fin, accion, parametros_json, activo)
            VALUES (?, ?, ?, ?, 'SOBRESCRIBIR', ?, 1);
        """, (name, rule_code, fecha_inicio, fecha_fin, params1))
        
    # Group 2: Mondays (Lunes=0)
    group2 = ['GRABOVIECKI FERNANDA']
    params2 = json.dumps([{"turnos": ["N", "M", "MT"], "dias": [0]}])
    
    for name in group2:
        print(f"Applying adjustment for {name} (Mondays)...")
        cursor.execute("""
            INSERT INTO personal_reglas_ajustes (personal_nombre, codigo_regla, fecha_inicio, fecha_fin, accion, parametros_json, activo)
            VALUES (?, ?, ?, ?, 'SOBRESCRIBIR', ?, 1);
        """, (name, rule_code, fecha_inicio, fecha_fin, params2))
        
    conn.commit()
    print("More adjustments applied successfully.")
    conn.close()

if __name__ == "__main__":
    apply_more_adjustments()
