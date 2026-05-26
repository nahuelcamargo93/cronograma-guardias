import sqlite3
import json

conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()

# 1. Inspect before
cursor.execute("""
    SELECT sr.id, rc.codigo_regla, sr.parametros_json
    FROM servicios_reglas sr
    JOIN reglas_catalogo rc ON sr.regla_id = rc.id
    WHERE sr.servicio_id = 2 AND rc.codigo_regla IN ('PESO_EQUIDAD_FINDES_ANUAL', 'PESO_EQUIDAD_FINDES_MENSUAL_CALENDARIO')
""")
rows = cursor.fetchall()
print("Before update:")
for r in rows:
    print(f"ID: {r[0]}, Rule: {r[1]}, Params: {r[2]}")

# 2. Update weights (multiply by 10)
for r in rows:
    sr_id = r[0]
    rule_code = r[1]
    params = json.loads(r[2])
    if 'peso' in params:
        old_peso = params['peso']
        params['peso'] = old_peso * 10
        new_params_json = json.dumps(params)
        cursor.execute("""
            UPDATE servicios_reglas
            SET parametros_json = ?
            WHERE id = ?
        """, (new_params_json, sr_id))
        print(f"Updated {rule_code}: {old_peso} -> {params['peso']}")

conn.commit()

# 3. Inspect after
cursor.execute("""
    SELECT sr.id, rc.codigo_regla, sr.parametros_json
    FROM servicios_reglas sr
    JOIN reglas_catalogo rc ON sr.regla_id = rc.id
    WHERE sr.servicio_id = 2 AND rc.codigo_regla IN ('PESO_EQUIDAD_FINDES_ANUAL', 'PESO_EQUIDAD_FINDES_MENSUAL_CALENDARIO')
""")
rows = cursor.fetchall()
print("\nAfter update:")
for r in rows:
    print(f"ID: {r[0]}, Rule: {r[1]}, Params: {r[2]}")

conn.close()
