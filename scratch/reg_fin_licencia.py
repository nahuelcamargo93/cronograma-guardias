import sqlite3
import json

def register_fin_licencia():
    conn = sqlite3.connect('cronograma_inteligente.db')
    cursor = conn.cursor()
    
    # 1. Registrar en el catálogo
    cursor.execute("""
        INSERT OR IGNORE INTO reglas_catalogo (codigo_regla, tipo, descripcion)
        VALUES ('FIN_LICENCIA', 'HARD', 'Obliga a trabajar el día inmediatamente posterior al fin de una licencia (LAR/LPP).')
    """)
    
    # 2. Asignar a Enfermería (ID: 2)
    cursor.execute("""
        INSERT OR IGNORE INTO servicios_reglas (servicio_id, regla_id, parametros_json)
        SELECT 2, id, '{}'
        FROM reglas_catalogo 
        WHERE codigo_regla = 'FIN_LICENCIA'
    """)
    
    conn.commit()
    conn.close()
    print("Regla FIN_LICENCIA registrada exitosamente en la DB.")

if __name__ == "__main__":
    register_fin_licencia()
