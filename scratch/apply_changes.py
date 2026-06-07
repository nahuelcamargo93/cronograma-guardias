import sqlite3
import os
import json

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cronograma_inteligente.db")
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

try:
    # 1. Obtener id del puesto Especial para el servicio 1
    cursor.execute("SELECT id FROM puestos WHERE nombre = 'Especial' AND servicio_id = 1")
    puesto_row = cursor.fetchone()
    if not puesto_row:
        raise ValueError("No se encontró el puesto 'Especial' para el servicio 1.")
    puesto_id = puesto_row[0]
    print(f"Puesto 'Especial' encontrado con ID: {puesto_id}")

    # 2. Insertar el turno Dia_especial en turnos_config
    # Verificamos si ya existe
    cursor.execute("SELECT id FROM turnos_config WHERE nombre = 'Dia_especial' AND servicio_id = 1")
    turno_row = cursor.fetchone()
    
    if not turno_row:
        cursor.execute("""
            INSERT INTO turnos_config (servicio_id, nombre, hora_inicio, horas, dias_semana, orden, activo, puesto_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (1, 'Dia_especial', '08:00', 12, '0,1,2,3,4,5,6', 10, 1, puesto_id))
        print("Turno 'Dia_especial' insertado correctamente.")
    else:
        cursor.execute("""
            UPDATE turnos_config 
            SET hora_inicio = '08:00', horas = 12, dias_semana = '0,1,2,3,4,5,6', orden = 10, activo = 1, puesto_id = ?
            WHERE id = ?
        """, (puesto_id, turno_row[0]))
        print("Turno 'Dia_especial' actualizado correctamente.")

    # 3. Actualizar la regla ASIGNACION_FIJA de Lic. Coniglio
    # Verificamos si existe el registro
    cursor.execute("""
        SELECT id, parametros_json FROM personal_reglas 
        WHERE personal_nombre = 'Lic. Coniglio' AND codigo_regla = 'ASIGNACION_FIJA'
    """)
    regla_row = cursor.fetchone()

    nuevo_json = json.dumps([
        {"Dia": "Miercoles", "Turno": "Dia_especial", "Tipo": "Especial", "Horas": 12}
    ])

    if regla_row:
        cursor.execute("""
            UPDATE personal_reglas 
            SET parametros_json = ? 
            WHERE id = ?
        """, (nuevo_json, regla_row[0]))
        print(f"Regla ASIGNACION_FIJA de Lic. Coniglio actualizada correctamente. JSON anterior: {regla_row[1]}")
    else:
        cursor.execute("""
            INSERT INTO personal_reglas (personal_nombre, codigo_regla, parametros_json, activo, servicio_id)
            VALUES (?, ?, ?, ?, ?)
        """, ('Lic. Coniglio', 'ASIGNACION_FIJA', nuevo_json, 1, 1))
        print("Regla ASIGNACION_FIJA de Lic. Coniglio creada correctamente.")

    conn.commit()
    print("Transacción guardada con éxito.")

except Exception as e:
    conn.rollback()
    print(f"Error al aplicar cambios: {e}")
finally:
    conn.close()
