import sqlite3

db_path = r"c:\Users\asus\Desktop\Ryoko\cronograma_inteligente\cronograma_inteligente.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # Activar CUMPLEANOS_LIBRE
    cursor.execute("""
        INSERT INTO servicios_reglas (servicio_id, codigo_regla, parametros_json, activo)
        VALUES (1, 'CUMPLEANOS_LIBRE', '{}', 1)
        ON CONFLICT(servicio_id, codigo_regla) DO UPDATE SET activo=1, parametros_json='{}'
    """)
    print("Regla CUMPLEANOS_LIBRE activada para el servicio 1.")

    # Activar DIA_MADRE_PADRE_LIBRE
    cursor.execute("""
        INSERT INTO servicios_reglas (servicio_id, codigo_regla, parametros_json, activo)
        VALUES (1, 'DIA_MADRE_PADRE_LIBRE', '{}', 1)
        ON CONFLICT(servicio_id, codigo_regla) DO UPDATE SET activo=1, parametros_json='{}'
    """)
    print("Regla DIA_MADRE_PADRE_LIBRE activada para el servicio 1.")

    conn.commit()
    print("Cambios guardados con éxito en la base de datos.")
except Exception as e:
    conn.rollback()
    print(f"Error al activar las reglas: {e}")
finally:
    conn.close()
