import sqlite3
import json

def init_limites():
    conn = sqlite3.connect('cronograma_inteligente.db')
    cursor = conn.cursor()
    
    # 1. Configuración de base para Enfermería (Servicio 2)
    # Ponemos límites amplios (0-144) para que no interfiera con la regla estricta de 144h
    params = {
        "MIN_HORAS_BASE": 0,
        "MAX_HORAS_LIMITE_BASE": 144,
        "SEMANAS_BASE": 4,
        "PESO_BRECHA_MENSUAL": 50
    }
    
    cursor.execute("""
        INSERT OR IGNORE INTO servicios_reglas (servicio_id, regla_id, parametros_json)
        SELECT 2, id, ?
        FROM reglas_catalogo 
        WHERE codigo_regla = 'LIMITES_SOFT_RULES'
    """, (json.dumps(params),))
    
    conn.commit()
    conn.close()
    print("Regla LIMITES_SOFT_RULES inicializada para Enfermería.")

if __name__ == "__main__":
    init_limites()
