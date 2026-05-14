import sqlite3
import json

conn = sqlite3.connect('cronograma_inteligente.db')

# Ver qué tiene Juarez actualmente
rows = conn.execute("""
    SELECT rc.codigo_regla, pr.parametros_json 
    FROM personal_reglas pr
    JOIN reglas_catalogo rc ON pr.regla_id = rc.id
    WHERE pr.personal_nombre = 'Lic. Juarez'
""").fetchall()
print("Reglas actuales de Juarez:")
for r in rows:
    print(f"  {r[0]}: {r[1]}")

# Obtener el regla_id de EXCLUIR_TURNOS
regla_id = conn.execute("SELECT id FROM reglas_catalogo WHERE codigo_regla = 'EXCLUIR_TURNOS'").fetchone()[0]

# Juarez ya tiene EXCLUIR_TURNOS con Mañana_especial y Tarde_especial (del script anterior)
# Necesitamos agregar Mañana_UTI y Mañana_UCO a esa lista
row = conn.execute("SELECT parametros_json FROM personal_reglas WHERE personal_nombre = 'Lic. Juarez' AND regla_id = ?", (regla_id,)).fetchone()

if row and row[0]:
    actual = json.loads(row[0])
    turnos_actuales = actual[0].get('turnos', []) if actual else []
else:
    turnos_actuales = []

print(f"\nTurnos prohibidos actuales: {turnos_actuales}")

# Agregar Mañana_UTI y Mañana_UCO si no están ya
for t in ["Mañana_UTI", "Mañana_UCO"]:
    if t not in turnos_actuales:
        turnos_actuales.append(t)

nuevo_params = json.dumps([{"turnos": turnos_actuales, "dias": [0,1,2,3,4,5,6]}])
conn.execute("""
    INSERT INTO personal_reglas (personal_nombre, regla_id, parametros_json)
    VALUES ('Lic. Juarez', ?, ?)
    ON CONFLICT(personal_nombre, regla_id) DO UPDATE SET parametros_json = excluded.parametros_json
""", (regla_id, nuevo_params))

conn.commit()
print(f"\nActualizado. Nuevos turnos prohibidos: {turnos_actuales}")
conn.close()
