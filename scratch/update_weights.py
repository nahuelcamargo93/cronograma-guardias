import sqlite3
import json

def update_weights():
    conn = sqlite3.connect('cronograma_inteligente.db')
    cursor = conn.cursor()
    
    # Pesos a actualizar
    nuevos_pesos = {
        'PESO_MIX_HORARIO': 3000,          # Subimos fuerte la penalización por mezclar en la semana
        'PESO_EQUIDAD_TIPO_TURNO': 1000,   # Subimos la penalización por no rotar equitativamente
        'PESO_INCONSISTENCIA': 500         # Subimos la penalización por saltos bruscos
    }
    
    for codigo, peso in nuevos_pesos.items():
        # Asegurar que la regla existe en el catálogo
        cursor.execute("INSERT OR IGNORE INTO reglas_catalogo (codigo_regla, tipo, descripcion) VALUES (?, 'SOFT', ?)", 
                       (codigo, f"Peso para {codigo}"))
        
        # Obtener ID
        cursor.execute("SELECT id FROM reglas_catalogo WHERE codigo_regla = ?", (codigo,))
        regla_id = cursor.fetchone()[0]
        
        # Actualizar peso para servicio 2
        cursor.execute("""
            INSERT OR REPLACE INTO servicios_reglas (servicio_id, regla_id, parametros_json)
            VALUES (2, ?, ?)
        """, (regla_id, json.dumps({"peso": peso})))
        
    conn.commit()
    conn.close()
    print("Pesos de consistencia actualizados (PESO_MIX_HORARIO=3000, PESO_EQUIDAD_TIPO_TURNO=1000).")

if __name__ == "__main__":
    update_weights()
