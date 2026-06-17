import sqlite3
import json

conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()

coordinadores_y_jefe = [
    "Garcia, Luciano",
    "Toledo, Andrea",
    "Franco, Leandro",
    "Moyano, Fernando"
]

print("=== Aplicando exclusión de turnos de 12 hs en días de semana ===")

for nombre in coordinadores_y_jefe:
    # Obtener el registro actual
    cursor.execute("SELECT parametros_json FROM personal_reglas WHERE personal_nombre = ? AND codigo_regla = 'EXCLUIR_TURNOS'", (nombre,))
    row = cursor.fetchone()
    
    if row:
        try:
            # Reemplazar posibles caracteres rotos antes de cargar el JSON
            raw_json = row[0]
            raw_json = raw_json.replace("Maana", "Mañana").replace("Ma\\u00f1ana", "Mañana")
            params = json.loads(raw_json)
        except Exception as e:
            print(f"Error al decodificar JSON para {nombre}: {e}. Se inicializará vacío.")
            params = []
            
        # Limpiar caracteres en los turnos existentes
        for item in params:
            if "turnos" in item:
                item["turnos"] = [t.replace("Maana", "Mañana") for t in item["turnos"]]
                
        # Agregar la exclusión de turnos de 12 hs de día durante días de semana (Lunes=0 a Viernes=4)
        excl_semana_12h = {
            "turnos": ["Dia_UTI", "Dia_UCO", "Dia_especial"],
            "dias": [0, 1, 2, 3, 4]
        }
        
        # Verificar si ya existe una regla similar para evitar duplicados
        ya_existe = False
        for item in params:
            if sorted(item.get("turnos", [])) == sorted(excl_semana_12h["turnos"]) and sorted(item.get("dias", [])) == sorted(excl_semana_12h["dias"]):
                ya_existe = True
                break
                
        if not ya_existe:
            params.append(excl_semana_12h)
            new_json = json.dumps(params, ensure_ascii=False)
            cursor.execute("UPDATE personal_reglas SET parametros_json = ? WHERE personal_nombre = ? AND codigo_regla = 'EXCLUIR_TURNOS'", (new_json, nombre))
            print(f"Actualizado: {nombre}")
            print(f"  Nuevo JSON: {new_json}")
        else:
            print(f"Ya existía la regla para {nombre}")
    else:
        # Si no existiera la regla (aunque ya vimos que sí existe), la creamos
        params = [{
            "turnos": ["Dia_UTI", "Dia_UCO", "Dia_especial"],
            "dias": [0, 1, 2, 3, 4]
        }]
        new_json = json.dumps(params, ensure_ascii=False)
        cursor.execute("INSERT INTO personal_reglas (personal_nombre, codigo_regla, parametros_json, activo, servicio_id) VALUES (?, 'EXCLUIR_TURNOS', ?, 1, 1)", (nombre, new_json))
        print(f"Creado: {nombre}")
        print(f"  JSON: {new_json}")

conn.commit()
conn.close()
print("\n=== Proceso completado ===")
