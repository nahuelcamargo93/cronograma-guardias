import sqlite3
import json

def final_fix():
    conn = sqlite3.connect('cronograma_inteligente.db')
    cursor = conn.cursor()
    
    # 1. Corregir nombres de turnos excluidos (G_Planta en lugar de 24hs)
    exclusion = json.dumps([{"turnos": ["G_Planta"], "dias": [0,1,2,3,4,5,6]}])
    nombres = ['Aguilera Graciela', 'Barloa Matías Damián', 'Garcia Rodriguez, Maria Eugenia.', 'Godoy Maria']
    for n in nombres:
        cursor.execute("UPDATE personal_reglas SET parametros_json = ? WHERE personal_nombre = ? AND regla_id = 4", (exclusion, n))
    
    # 2. Asegurar que las reglas de servicio 3 estén bien
    cursor.execute("INSERT OR REPLACE INTO servicios_reglas (servicio_id, regla_id, parametros_json) VALUES (3, 169, ?)", (json.dumps({"min_horas": 144}),))
    cursor.execute("INSERT OR REPLACE INTO servicios_reglas (servicio_id, regla_id, parametros_json) VALUES (3, 167, ?)", (json.dumps({"por_turno": {"G": 48, "D": 24, "N": 24}}),))
    
    conn.commit()
    conn.close()
    print("Final database fixes applied.")

if __name__ == "__main__":
    final_fix()
