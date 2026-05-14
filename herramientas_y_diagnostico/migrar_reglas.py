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
        ('PESO_EQUIDAD_FINDES', {"peso": 1000}),
        ('PESO_BRECHA_ANUAL', {"peso": 100}),
        ('PESO_BRECHA_MENSUAL', {"peso": 50}),
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
        res = cursor.execute("SELECT id FROM reglas_catalogo WHERE codigo_regla = ?", (codigo,)).fetchone()
        if res:
            regla_id = res[0]
            cursor.execute("""
                INSERT INTO servicios_reglas (servicio_id, regla_id, parametros_json)
                VALUES (1, ?, ?)
                ON CONFLICT(servicio_id, regla_id) DO UPDATE SET parametros_json = excluded.parametros_json
            """, (regla_id, json.dumps(params)))

    print("\n--- Migrando Reglas de Personal ---")
    for p_data in data.PERSONAL:
        nombre = p_data['Nombre']
        
        # Obtener mapeo de reglas por código
        def get_regla_id(cod):
            res = cursor.execute("SELECT id FROM reglas_catalogo WHERE codigo_regla = ?", (cod,)).fetchone()
            return res[0] if res else None

        # 1. Puede_Noche -> NO_NOCHES o MAX_NOCHES
        if not p_data.get('Puede_Noche', True):
            rid = get_regla_id('NO_NOCHES')
            if rid:
                cursor.execute("""
                    INSERT INTO personal_reglas (personal_nombre, regla_id, parametros_json) 
                    VALUES (?, ?, ?)
                    ON CONFLICT(personal_nombre, regla_id) DO UPDATE SET parametros_json = excluded.parametros_json
                """, (nombre, rid, json.dumps({})))
        else:
            max_n = p_data.get('Max_Noches', 4)
            rid = get_regla_id('MAX_NOCHES')
            if rid:
                cursor.execute("""
                    INSERT INTO personal_reglas (personal_nombre, regla_id, parametros_json) 
                    VALUES (?, ?, ?)
                    ON CONFLICT(personal_nombre, regla_id) DO UPDATE SET parametros_json = excluded.parametros_json
                """, (nombre, rid, json.dumps({"limite": max_n})))

        # 2. Turnos_Prohibidos_LV
        prohibidos = p_data.get('Turnos_Prohibidos_LV', [])
        if prohibidos:
            rid = get_regla_id('EXCLUIR_TURNOS')
            if rid:
                params = {"turnos": prohibidos, "dias": [0,1,2,3,4]} # Lunes a Viernes
                cursor.execute("""
                    INSERT INTO personal_reglas (personal_nombre, regla_id, parametros_json) 
                    VALUES (?, ?, ?)
                    ON CONFLICT(personal_nombre, regla_id) DO UPDATE SET parametros_json = excluded.parametros_json
                """, (nombre, rid, json.dumps(params)))

        # 3. Semanas_Seguimiento
        seguimientos = p_data.get('Semanas_Seguimiento', {})
        if seguimientos:
            rid = get_regla_id('SEMANA_SEGUIMIENTO')
            if rid:
                params_list = [{"tipo": t, "semanas": s} for t, s in seguimientos.items()]
                cursor.execute("""
                    INSERT INTO personal_reglas (personal_nombre, regla_id, parametros_json) 
                    VALUES (?, ?, ?)
                    ON CONFLICT(personal_nombre, regla_id) DO UPDATE SET parametros_json = excluded.parametros_json
                """, (nombre, rid, json.dumps(params_list)))

        # 4. Asignaciones_Fijas
        asig_fijas = p_data.get('Asignaciones_Fijas', [])
        if asig_fijas:
            rid = get_regla_id('ASIGNACION_FIJA')
            if rid:
                cursor.execute("""
                    INSERT INTO personal_reglas (personal_nombre, regla_id, parametros_json) 
                    VALUES (?, ?, ?)
                    ON CONFLICT(personal_nombre, regla_id) DO UPDATE SET parametros_json = excluded.parametros_json
                """, (nombre, rid, json.dumps(asig_fijas)))

        # 5. Turnos_Preferenciales (SOFT)
        preferencias = p_data.get('Turnos_Preferenciales', [])
        if preferencias:
            rid = get_regla_id('TURNOS_PREFERENCIALES')
            if rid:
                cursor.execute("""
                    INSERT INTO personal_reglas (personal_nombre, regla_id, parametros_json) 
                    VALUES (?, ?, ?)
                    ON CONFLICT(personal_nombre, regla_id) DO UPDATE SET parametros_json = excluded.parametros_json
                """, (nombre, rid, json.dumps(preferencias)))

    conn.commit()
    conn.close()
    print("\nMigracion completada con exito.")

if __name__ == "__main__":
    migrar()
