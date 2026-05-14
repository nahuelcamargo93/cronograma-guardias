import sqlite3
import json

conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()

# 1. Buscar la regla
cursor.execute("SELECT sr.regla_id, sr.parametros_json FROM servicios_reglas sr JOIN reglas_catalogo rc ON sr.regla_id = rc.id WHERE sr.servicio_id = 2 AND rc.codigo_regla = 'MIN_HORAS_MES_CALENDARIO'")
row = cursor.fetchone()

if row:
    regla_id, params_str = row
    params = json.loads(params_str)
    params['min_horas'] = 132
    cursor.execute("UPDATE servicios_reglas SET parametros_json = ? WHERE servicio_id = 2 AND regla_id = ?", (json.dumps(params), regla_id))
    print(f"Horas mínimas actualizadas a 132 para Servicio 2 (antes: {params_str})")
else:
    # Si no existe, la creamos (primero buscamos el ID en el catálogo)
    cursor.execute("SELECT id FROM reglas_catalogo WHERE codigo_regla = 'MIN_HORAS_MES_CALENDARIO'")
    cat_row = cursor.fetchone()
    if cat_row:
        regla_id = cat_row[0]
        params = {"min_horas": 132, "peso": 100}
        cursor.execute("INSERT INTO servicios_reglas (servicio_id, regla_id, parametros_json) VALUES (?, ?, ?)", (2, regla_id, json.dumps(params)))
        print("Regla MIN_HORAS_MES_CALENDARIO creada con 132 horas para Servicio 2")
    else:
        print("Error: No se encontró MIN_HORAS_MES_CALENDARIO en el catálogo")

conn.commit()
conn.close()
