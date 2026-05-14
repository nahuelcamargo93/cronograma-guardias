import sqlite3
import json

def update_fathers():
    conn = sqlite3.connect('cronograma_inteligente.db')
    cursor = conn.cursor()
    
    papas = [
        "CORSO ARTURO",
        "ARCE DANIEL",
        "VELEZ DANIEL",
        "ESCUDERO SERGIO",
        "PALACIOS FACUNDO"
    ]
    
    # 1. Actualizar bandera es_padre
    for nombre in papas:
        cursor.execute("UPDATE personal SET es_padre = 1 WHERE nombre = ? AND servicio_id = 2", (nombre,))
        if cursor.rowcount == 0:
            print(f"Advertencia: No se encontró a {nombre} en enfermería.")
        else:
            print(f"Actualizado: {nombre} marcado como padre.")
            
    # 2. Asegurar que la regla DIA_MADRE_PADRE_LIBRE esté activa para el servicio 2
    cursor.execute("SELECT id FROM reglas_catalogo WHERE codigo_regla = 'DIA_MADRE_PADRE_LIBRE'")
    regla = cursor.fetchone()
    if regla:
        regla_id = regla[0]
        # Insertar si no existe
        cursor.execute("""
            INSERT OR IGNORE INTO servicios_reglas (servicio_id, regla_id, parametros_json)
            VALUES (2, ?, ?)
        """, (regla_id, json.dumps({"activo": True})))
        print("Regla DIA_MADRE_PADRE_LIBRE asegurada para el servicio 2.")
    
    conn.commit()
    conn.close()
    print("Base de datos actualizada con éxito.")

if __name__ == "__main__":
    update_fathers()
