import sqlite3
import json
import shutil
import os

DB_NAME = 'cronograma_inteligente.db'
BACKUP_NAME = 'cronograma_inteligente_backup_turnos.db'

# 1. Realizar respaldo
print(f"Creando copia de seguridad de {DB_NAME} en {BACKUP_NAME}...")
shutil.copyfile(DB_NAME, BACKUP_NAME)
if os.path.exists(BACKUP_NAME):
    print("Respaldo creado con éxito.")
else:
    raise FileNotFoundError("No se pudo crear el respaldo de la base de datos.")

# Mapeo de nombres de turnos viejos a nuevos
REEMPLAZOS = {
    "G_Planta": "Guardia_Planta",
    "D_Planta": "Dia_Planta",
    "N_Planta": "Noche_Planta",
    "G_Residente": "Guardia_Residente",
    "D_Residente": "Dia_Residente",
    "N_Residente": "Noche_Residente"
}

def reemplazar_nombres_en_objeto(obj):
    """Reemplaza recursivamente los nombres antiguos de turnos en objetos JSON cargados (dict, list, str)."""
    if isinstance(obj, dict):
        new_dict = {}
        for k, v in obj.items():
            # Si la clave es un nombre antiguo de turno, la reemplazamos
            new_key = REEMPLAZOS.get(k, k)
            new_dict[new_key] = reemplazar_nombres_en_objeto(v)
        return new_dict
    elif isinstance(obj, list):
        return [reemplazar_nombres_en_objeto(x) for x in obj]
    elif isinstance(obj, str):
        return REEMPLAZOS.get(obj, obj)
    return obj

def procesar_json_string(json_str):
    """Intenta cargar el JSON, realizar los reemplazos y serializarlo nuevamente."""
    if not json_str:
        return json_str
    try:
        data = json.loads(json_str)
        updated_data = reemplazar_nombres_en_objeto(data)
        return json.dumps(updated_data, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error parseando JSON: {e}")
        # Retorno de fallback textual si fallara el parsing estructurado (reemplazo simple de subcadenas)
        res = json_str
        for viejo, nuevo in REEMPLAZOS.items():
            res = res.replace(f'"{viejo}"', f'"{nuevo}"')
        return res

conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()

try:
    # --- 1. SERVICIOS REGLAS ---
    print("\nActualizando servicios_reglas (servicio_id = 3)...")
    cursor.execute("SELECT rowid, codigo_regla, parametros_json FROM servicios_reglas WHERE servicio_id = 3")
    serv_reglas = cursor.fetchall()
    cambios_serv = 0
    for rowid, codigo, params in serv_reglas:
        if params:
            nuevos_params = procesar_json_string(params)
            if nuevos_params != params:
                cursor.execute(
                    "UPDATE servicios_reglas SET parametros_json = ? WHERE rowid = ?",
                    (nuevos_params, rowid)
                )
                print(f" -> Actualizada regla de servicio: {codigo}")
                cambios_serv += 1
    print(f"Total servicios_reglas modificadas: {cambios_serv}")

    # --- 2. SERVICIOS REGLAS AJUSTES ---
    print("\nActualizando servicios_reglas_ajustes (servicio_id = 3)...")
    cursor.execute("SELECT rowid, codigo_regla, parametros_json FROM servicios_reglas_ajustes WHERE servicio_id = 3")
    serv_ajustes = cursor.fetchall()
    cambios_serv_aj = 0
    for rowid, codigo, params in serv_ajustes:
        if params:
            nuevos_params = procesar_json_string(params)
            if nuevos_params != params:
                cursor.execute(
                    "UPDATE servicios_reglas_ajustes SET parametros_json = ? WHERE rowid = ?",
                    (nuevos_params, rowid)
                )
                print(f" -> Actualizado ajuste de regla de servicio: {codigo}")
                cambios_serv_aj += 1
    print(f"Total servicios_reglas_ajustes modificados: {cambios_serv_aj}")

    # --- 3. PERSONAL REGLAS ---
    print("\nActualizando personal_reglas para personal del servicio_id = 3...")
    cursor.execute("""
        SELECT pr.rowid, pr.personal_nombre, pr.codigo_regla, pr.parametros_json 
        FROM personal_reglas pr
        JOIN personal p ON pr.personal_nombre = p.nombre
        WHERE p.servicio_id = 3
    """)
    pers_reglas = cursor.fetchall()
    cambios_pers = 0
    for rowid, nombre, codigo, params in pers_reglas:
        if params:
            nuevos_params = procesar_json_string(params)
            if nuevos_params != params:
                cursor.execute(
                    "UPDATE personal_reglas SET parametros_json = ? WHERE rowid = ?",
                    (nuevos_params, rowid)
                )
                cambios_pers += 1
    print(f"Total personal_reglas modificadas: {cambios_pers}")

    # --- 4. PERSONAL REGLAS AJUSTES ---
    print("\nActualizando personal_reglas_ajustes para personal del servicio_id = 3...")
    cursor.execute("""
        SELECT pra.rowid, pra.personal_nombre, pra.codigo_regla, pra.parametros_json 
        FROM personal_reglas_ajustes pra
        JOIN personal p ON pra.personal_nombre = p.nombre
        WHERE p.servicio_id = 3
    """)
    pers_ajustes = cursor.fetchall()
    cambios_pers_aj = 0
    for rowid, nombre, codigo, params in pers_ajustes:
        if params:
            nuevos_params = procesar_json_string(params)
            if nuevos_params != params:
                cursor.execute(
                    "UPDATE personal_reglas_ajustes SET parametros_json = ? WHERE rowid = ?",
                    (nuevos_params, rowid)
                )
                cambios_pers_aj += 1
    print(f"Total personal_reglas_ajustes modificados: {cambios_pers_aj}")

    conn.commit()
    print("\n[OK] ¡Migración de nombres de turnos completada con éxito en la base de datos!")

except Exception as err:
    conn.rollback()
    print(f"\n[ERROR] Ocurrió un error en la migración: {err}")
    print("Se realizó un rollback de los cambios.")
finally:
    conn.close()
