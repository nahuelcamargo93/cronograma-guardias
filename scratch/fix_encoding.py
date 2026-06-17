import sqlite3

conn = sqlite3.connect('cronograma_inteligente.db')
cursor = conn.cursor()

# Obtener todos los registros de personal_reglas
cursor.execute("SELECT id, personal_nombre, codigo_regla, parametros_json FROM personal_reglas")
rows = cursor.fetchall()

print("=== Corrigiendo codificación en personal_reglas ===")
for r_id, nombre, codigo, params_json in rows:
    if params_json:
        # Reemplazar caracteres dañados o codificaciones alternativas
        fixed_json = params_json.replace("Maana", "Mañana").replace("Ma\\u00f1ana", "Mañana").replace("Ma\u00f1ana", "Mañana")
        if fixed_json != params_json:
            cursor.execute("UPDATE personal_reglas SET parametros_json = ? WHERE id = ?", (fixed_json, r_id))
            print(f"Corregido ID {r_id} ({nombre} - {codigo}):")
            print(f"  Antes: {repr(params_json)}")
            print(f"  Ahora: {repr(fixed_json)}")

conn.commit()
conn.close()
print("=== Codificación corregida ===")
