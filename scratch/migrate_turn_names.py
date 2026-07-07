import database.connection as c
import json

conn = c.get_connection()
cursor = conn.cursor()

replacements = {
    "D_Planta": "Dia_Planta",
    "N_Planta": "Noche_Planta",
    "G_Planta": "Guardia_Planta",
    "D_Residente": "Dia_Residente",
    "N_Residente": "Noche_Residente",
    "G_Residente": "Guardia_Residente"
}

def replace_in_obj(obj):
    if isinstance(obj, str):
        return replacements.get(obj, obj)
    elif isinstance(obj, list):
        return [replace_in_obj(x) for x in obj]
    elif isinstance(obj, dict):
        new_dict = {}
        for k, v in obj.items():
            new_key = replacements.get(k, k)
            new_val = replace_in_obj(v)
            new_dict[new_key] = new_val
        return new_dict
    return obj

def process_json(json_str):
    if not json_str:
        return json_str
    try:
        obj = json.loads(json_str)
        new_obj = replace_in_obj(obj)
        return json.dumps(new_obj, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error parsing JSON: {e}")
        return json_str

# 1. servicios_reglas
print("=== Updating servicios_reglas ===")
rows = cursor.execute("SELECT id, codigo_regla, parametros_json FROM servicios_reglas WHERE servicio_id = 3").fetchall()
for r_id, code, params in rows:
    new_params = process_json(params)
    if params != new_params:
        print(f"Update Rule {code} (ID {r_id}):\nFROM: {params.strip()}\nTO: {new_params.strip()}\n")
        cursor.execute("UPDATE servicios_reglas SET parametros_json = ? WHERE id = ?", (new_params, r_id))

# 2. personal_reglas
print("=== Updating personal_reglas ===")
rows = cursor.execute("""
    SELECT pr.id, pr.personal_nombre, pr.codigo_regla, pr.parametros_json 
    FROM personal_reglas pr
    JOIN personal p ON pr.personal_nombre = p.nombre
    WHERE p.servicio_id = 3
""").fetchall()
for r_id, p_name, code, params in rows:
    new_params = process_json(params)
    if params != new_params:
        print(f"Update Personal Rule {code} for {p_name} (ID {r_id}):\nFROM: {params.strip()}\nTO: {new_params.strip()}\n")
        cursor.execute("UPDATE personal_reglas SET parametros_json = ? WHERE id = ?", (new_params, r_id))

# 3. servicios_reglas_ajustes
print("=== Updating servicios_reglas_ajustes ===")
rows = cursor.execute("SELECT id, codigo_regla, parametros_json FROM servicios_reglas_ajustes WHERE servicio_id = 3").fetchall()
for r_id, code, params in rows:
    new_params = process_json(params)
    if params != new_params:
        print(f"Update Service Rule Ajuste {code} (ID {r_id}):\nFROM: {params.strip()}\nTO: {new_params.strip()}\n")
        cursor.execute("UPDATE servicios_reglas_ajustes SET parametros_json = ? WHERE id = ?", (new_params, r_id))

# 4. personal_reglas_ajustes
print("=== Updating personal_reglas_ajustes ===")
rows = cursor.execute("""
    SELECT pra.id, pra.personal_nombre, pra.codigo_regla, pra.parametros_json 
    FROM personal_reglas_ajustes pra
    JOIN personal p ON pra.personal_nombre = p.nombre
    WHERE p.servicio_id = 3
""").fetchall()
for r_id, p_name, code, params in rows:
    new_params = process_json(params)
    if params != new_params:
        print(f"Update Personal Rule Ajuste {code} for {p_name} (ID {r_id}):\nFROM: {params.strip()}\nTO: {new_params.strip()}\n")
        cursor.execute("UPDATE personal_reglas_ajustes SET parametros_json = ? WHERE id = ?", (new_params, r_id))

conn.commit()
print("Migration completed and committed successfully.")
conn.close()
