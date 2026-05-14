import sqlite3
import json

def apply_adjustments():
    conn = sqlite3.connect('cronograma_inteligente.db')
    cursor = conn.cursor()
    
    names = ['OLGUIN LUCIA', 'NIEVAS CARLA', 'BORIA MAYRA']
    rule_code = 'EXCLUIR_TURNOS'
    fecha_inicio = '2026-05-01'
    fecha_fin = '2026-12-31'
    params = json.dumps([{"turnos": ["T"], "dias": [1]}])
    
    for name in names:
        print(f"Applying adjustment for {name}...")
        # Check if already exists to avoid duplicates
        cursor.execute("""
            SELECT id FROM personal_reglas_ajustes 
            WHERE personal_nombre = ? AND codigo_regla = ? AND fecha_inicio = ? AND fecha_fin = ?;
        """, (name, rule_code, fecha_inicio, fecha_fin))
        
        if cursor.fetchone():
            print(f"Adjustment already exists for {name}.")
        else:
            cursor.execute("""
                INSERT INTO personal_reglas_ajustes (personal_nombre, codigo_regla, fecha_inicio, fecha_fin, accion, parametros_json, activo)
                VALUES (?, ?, ?, ?, 'SOBRESCRIBIR', ?, 1);
            """, (name, rule_code, fecha_inicio, fecha_fin, params))
            
    conn.commit()
    print("Adjustments applied successfully.")
    conn.close()

if __name__ == "__main__":
    apply_adjustments()
