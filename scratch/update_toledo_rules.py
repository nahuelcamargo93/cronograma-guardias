import sqlite3
import json

conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()

try:
    nombre = 'Toledo, Andrea'
    
    # 1. Desactivar MIN_TURNOS de Toledo, Andrea
    cursor.execute("""
        UPDATE personal_reglas 
        SET activo = 0 
        WHERE personal_nombre = ? AND codigo_regla = 'MIN_TURNOS'
    """, (nombre,))
    print(f"Desactivada regla MIN_TURNOS para {nombre}.")

    # 2. Agregar o actualizar ASIGNACION_FIJA para Toledo, Andrea
    asig_fija_json = json.dumps([
        {"Dia": "Lunes", "Turno": "Mañana_UCO"},
        {"Dia": "Martes", "Turno": "Mañana_UCO"},
        {"Dia": "Miercoles", "Turno": "Mañana_UCO"},
        {"Dia": "Jueves", "Turno": "Mañana_UCO"},
        {"Dia": "Viernes", "Turno": "Mañana_UCO"}
    ], ensure_ascii=False)

    # Verificar si existe
    cursor.execute("""
        SELECT id FROM personal_reglas 
        WHERE personal_nombre = ? AND codigo_regla = 'ASIGNACION_FIJA'
    """, (nombre,))
    row = cursor.fetchone()
    
    if row:
        cursor.execute("""
            UPDATE personal_reglas 
            SET parametros_json = ?, activo = 1 
            WHERE id = ?
        """, (asig_fija_json, row[0]))
        print(f"Actualizada regla ASIGNACION_FIJA existente (ID {row[0]}) para {nombre}.")
    else:
        cursor.execute("""
            INSERT INTO personal_reglas (personal_nombre, codigo_regla, parametros_json, activo, servicio_id)
            VALUES (?, 'ASIGNACION_FIJA', ?, 1, 1)
        """, (nombre, asig_fija_json))
        print(f"Creada regla ASIGNACION_FIJA para {nombre}.")

    conn.commit()
    print("Transacción confirmada con éxito.")

except Exception as e:
    conn.rollback()
    print("Error al actualizar la base de datos:", e)
finally:
    conn.close()
