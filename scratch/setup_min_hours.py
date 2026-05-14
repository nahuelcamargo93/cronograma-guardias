import sqlite3
import json

def setup_min_hours():
    conn = sqlite3.connect('cronograma_inteligente.db')
    cursor = conn.cursor()
    
    # 1. Registrar en el catálogo si no existe
    cursor.execute("""
        INSERT OR IGNORE INTO reglas_catalogo (codigo_regla, tipo, descripcion)
        VALUES ('MIN_HORAS_MES_CALENDARIO', 'HARD', 'Mínimo de horas trabajadas más licencias por mes calendario.')
    """)
    
    # 2. Obtener el ID de la regla
    cursor.execute("SELECT id FROM reglas_catalogo WHERE codigo_regla = 'MIN_HORAS_MES_CALENDARIO'")
    regla_id = cursor.fetchone()[0]
    
    # 3. Asignar al servicio 2 (Enfermería)
    cursor.execute("""
        INSERT OR REPLACE INTO servicios_reglas (servicio_id, regla_id, parametros_json)
        VALUES (2, ?, ?)
    """, (regla_id, json.dumps({"min_horas": 120})))
    
    conn.commit()
    conn.close()
    print("Regla MIN_HORAS_MES_CALENDARIO configurada con 120hs para Enfermería.")

if __name__ == "__main__":
    setup_min_hours()
