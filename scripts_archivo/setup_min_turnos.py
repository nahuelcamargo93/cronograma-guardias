import sqlite3
import json

conn = sqlite3.connect('cronograma_inteligente.db')

# 1. Eliminar SEMANA_SEGUIMIENTO del catálogo y referencias
ids = [r[0] for r in conn.execute(
    "SELECT id FROM reglas_catalogo WHERE codigo_regla = 'SEMANA_SEGUIMIENTO'"
).fetchall()]

if ids:
    placeholders = ','.join('?' * len(ids))
    conn.execute(f"DELETE FROM personal_reglas WHERE regla_id IN ({placeholders})", ids)
    conn.execute(f"DELETE FROM servicios_reglas WHERE regla_id IN ({placeholders})", ids)
    conn.execute(f"DELETE FROM organizaciones_reglas WHERE regla_id IN ({placeholders})", ids)
    conn.execute(f"DELETE FROM reglas_catalogo WHERE id IN ({placeholders})", ids)

# 2. Agregar MIN_TURNOS al catálogo
conn.execute("""
    INSERT OR IGNORE INTO reglas_catalogo (codigo_regla, tipo, descripcion)
    VALUES (
        'MIN_TURNOS',
        'HARD',
        'Limite minimo de un tipo de turno especifico por bloque semanal. JSON: [{"turno": "Mañana_UTI", "min_por_semana": 4}]'
    )
""")

regla_id = conn.execute("SELECT id FROM reglas_catalogo WHERE codigo_regla = 'MIN_TURNOS'").fetchone()[0]

# 3. Configurar MIN_TURNOS para Garcia, Franco, Moyano (Mañana_UTI)
params_uti = json.dumps([{"turno": "Mañana_UTI", "min_por_semana": 4}])
for persona in ["Lic. Garcia", "Lic. Franco", "Lic. Moyano"]:
    conn.execute("""
        INSERT INTO personal_reglas (personal_nombre, regla_id, parametros_json)
        VALUES (?, ?, ?)
        ON CONFLICT(personal_nombre, regla_id) DO UPDATE SET parametros_json = excluded.parametros_json
    """, (persona, regla_id, params_uti))

# 4. Configurar MIN_TURNOS para Toledo (Mañana_UCO)
params_uco = json.dumps([{"turno": "Mañana_UCO", "min_por_semana": 4}])
conn.execute("""
    INSERT INTO personal_reglas (personal_nombre, regla_id, parametros_json)
    VALUES ('Lic. Toledo', ?, ?)
    ON CONFLICT(personal_nombre, regla_id) DO UPDATE SET parametros_json = excluded.parametros_json
""", (regla_id, params_uco))

conn.commit()
print("Base de datos actualizada con MIN_TURNOS")
conn.close()
