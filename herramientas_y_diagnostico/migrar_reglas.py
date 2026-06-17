import json
import sqlite3
import data
import db

def migrar():
    # Asegurar que la DB esté inicializada y con el catálogo completo
    db.inicializar_db()
    db.inicializar_catalogo_reglas()
    
    conn = db.get_connection()
    cursor = conn.cursor()
    
    print("--- Sincronizando Organizaciones y Servicios ---")
    # Asumimos que HCRC es la organización 1 y Kinesiología Crítica es el servicio 1
    cursor.execute("INSERT OR IGNORE INTO organizaciones (id, nombre) VALUES (1, 'HCRC')")
    cursor.execute("INSERT OR IGNORE INTO servicios (id, organizacion_id, nombre) VALUES (1, 1, 'Kinesiologia Critica')")
    
    print("\n--- Sincronizando Personal ---")
    for p_data in data.PERSONAL:
        nombre = p_data['Nombre']
        rol = p_data['Rol']
        cursor.execute("""
            INSERT INTO personal (nombre, rol, servicio_id) 
            VALUES (?, ?, 1)
            ON CONFLICT(nombre) DO UPDATE SET rol = excluded.rol, servicio_id = 1
        """, (nombre, rol))
        
    print("\n--- Migrando Reglas de Servicio (Globales y Pesos) ---")
    # Reglas base y pesos para el servicio 1
    reglas_servicio = [
        ('MAX_HORAS_SEMANA', {"limite": 36}),
        ('DESC_POST_NOCHE', {"horas": 24}),
        ('PESO_BRECHA_ANUAL', {"peso": 100}),
        ('PESO_BRECHA_MENSUAL', {"peso": 50}),
        ('PESO_BRECHA_HORAS', {"peso": 20, "fecha_inicio": "2026-06-22"}),
        ('PESO_BRECHA_SEG', {"peso": 100}),
        ('PESO_EQUIDAD_FL3', {"peso": 500}),
        ('PESO_EQUIDAD_FL4', {"peso": 500}),
        ('BONUS_SEG_TOTAL', {"peso": 150}),
        ('BONUS_SEG_PUNTOS', {"peso": 5}),
        ('BONUS_COMBO_FINDE', {"peso": 15}),
        ('BONUS_PREFERENCIAS', {"peso": 300}),
        ('PESO_MIX_HORARIO', {"peso": 500}),
        ('PESO_INCONSISTENCIA', {"peso": 100})
    ]
    
    for codigo, params in reglas_servicio:
        cursor.execute("""
            INSERT INTO servicios_reglas (servicio_id, codigo_regla, parametros_json)
            VALUES (1, ?, ?)
            ON CONFLICT(servicio_id, codigo_regla) DO UPDATE SET parametros_json = excluded.parametros_json
        """, (codigo, json.dumps(params)))

    print("\n--- Migrando Reglas de Personal ---")
    for p_data in data.PERSONAL:
        nombre = p_data['Nombre']

        # 1. Puede_Noche -> NO_NOCHES o MAX_NOCHES
        if not p_data.get('Puede_Noche', True):
            cursor.execute("""
                INSERT INTO personal_reglas (personal_nombre, codigo_regla, parametros_json) 
                VALUES (?, 'NO_NOCHES', ?)
                ON CONFLICT(personal_nombre, codigo_regla) DO UPDATE SET parametros_json = excluded.parametros_json
            """, (nombre, json.dumps({})))
        else:
            max_n = p_data.get('Max_Noches', 4)
            cursor.execute("""
                INSERT INTO personal_reglas (personal_nombre, codigo_regla, parametros_json) 
                VALUES (?, 'MAX_NOCHES', ?)
                ON CONFLICT(personal_nombre, codigo_regla) DO UPDATE SET parametros_json = excluded.parametros_json
            """, (nombre, json.dumps({"limite": max_n})))

        # 2. Turnos_Prohibidos_LV
        prohibidos = p_data.get('Turnos_Prohibidos_LV', [])
        if prohibidos:
            params = {"turnos": prohibidos, "dias": [0,1,2,3,4]} # Lunes a Viernes
            cursor.execute("""
                INSERT INTO personal_reglas (personal_nombre, codigo_regla, parametros_json) 
                VALUES (?, 'EXCLUIR_TURNOS', ?)
                ON CONFLICT(personal_nombre, codigo_regla) DO UPDATE SET parametros_json = excluded.parametros_json
            """, (nombre, json.dumps(params)))

        # 3. Semanas_Seguimiento
        seguimientos = p_data.get('Semanas_Seguimiento', {})
        if seguimientos:
            params_list = [{"tipo": t, "semanas": s} for t, s in seguimientos.items()]
            cursor.execute("""
                INSERT INTO personal_reglas (personal_nombre, codigo_regla, parametros_json) 
                VALUES (?, 'SEMANA_SEGUIMIENTO', ?)
                ON CONFLICT(personal_nombre, codigo_regla) DO UPDATE SET parametros_json = excluded.parametros_json
            """, (nombre, json.dumps(params_list)))

        # 4. Asignaciones_Fijas
        asig_fijas = p_data.get('Asignaciones_Fijas', [])
        if asig_fijas:
            cursor.execute("""
                INSERT INTO personal_reglas (personal_nombre, codigo_regla, parametros_json) 
                VALUES (?, 'ASIGNACION_FIJA', ?)
                ON CONFLICT(personal_nombre, codigo_regla) DO UPDATE SET parametros_json = excluded.parametros_json
            """, (nombre, json.dumps(asig_fijas)))

        # 5. Turnos_Preferenciales (SOFT)
        preferencias = p_data.get('Turnos_Preferenciales', [])
        if preferencias:
            cursor.execute("""
                INSERT INTO personal_reglas (personal_nombre, codigo_regla, parametros_json) 
                VALUES (?, 'TURNOS_PREFERENCIALES', ?)
                ON CONFLICT(personal_nombre, codigo_regla) DO UPDATE SET parametros_json = excluded.parametros_json
            """, (nombre, json.dumps(preferencias)))

    conn.commit()
    conn.close()
    print("\nMigracion completada con exito.")

if __name__ == "__main__":
    migrar()
