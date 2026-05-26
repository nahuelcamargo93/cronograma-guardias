import sqlite3
import json

conn = sqlite3.connect('cronograma_inteligente.db')
cur = conn.cursor()

print("1. Inserting EXACTO_FINDES_MES and EXACTO_DIA_ESPECIFICO_MES into reglas_catalogo...")
cur.execute("""
    INSERT OR IGNORE INTO reglas_catalogo (codigo_regla, tipo, descripcion)
    VALUES ('EXACTO_FINDES_MES', 'HARD', 'Asegura que el personal tenga exactamente N fines de semana trabajados en el mes.')
""")
cur.execute("""
    INSERT OR IGNORE INTO reglas_catalogo (codigo_regla, tipo, descripcion)
    VALUES ('EXACTO_DIA_ESPECIFICO_MES', 'HARD', 'Asegura que el personal trabaje exactamente N veces un dia de la semana especifico en el mes. JSON: {"dia_semana": "Viernes", "exacto_dias": 1}')
""")

# Get the rule IDs
cur.execute("SELECT id FROM reglas_catalogo WHERE codigo_regla = 'MIN_FINDES_MES'")
min_findes_id = cur.fetchone()[0]

cur.execute("SELECT id FROM reglas_catalogo WHERE codigo_regla = 'EXACTO_FINDES_MES'")
exacto_findes_id = cur.fetchone()[0]

cur.execute("SELECT id FROM reglas_catalogo WHERE codigo_regla = 'MIN_DIA_ESPECIFICO_MES'")
min_dia_id = cur.fetchone()[0]

cur.execute("SELECT id FROM reglas_catalogo WHERE codigo_regla = 'EXACTO_DIA_ESPECIFICO_MES'")
exacto_dia_id = cur.fetchone()[0]

print("2. Enabling 'dinamico_licencias' on MIN_FINDES_MES for Service 3...")
cur.execute("""
    UPDATE servicios_reglas
    SET parametros_json = ?
    WHERE servicio_id = 3 AND regla_id = ?
""", (json.dumps({"min_findes": 2, "dinamico_licencias": True}), min_findes_id))

print("3. Enabling 'dinamico_licencias' on MIN_DIA_ESPECIFICO_MES for Service 3...")
cur.execute("""
    UPDATE servicios_reglas
    SET parametros_json = ?
    WHERE servicio_id = 3 AND regla_id = ?
""", (json.dumps({"dia_semana": "Viernes", "min_dias": 1, "dinamico_licencias": True}), min_dia_id))

print("4. Provisioning EXACTO_FINDES_MES for Service 3 (suspended by default)...")
cur.execute("""
    INSERT OR IGNORE INTO servicios_reglas (servicio_id, regla_id, parametros_json)
    VALUES (3, ?, ?)
""", (exacto_findes_id, json.dumps({"exacto_findes": 2, "dinamico_licencias": True, "suspendida": True})))

print("5. Provisioning EXACTO_DIA_ESPECIFICO_MES for Service 3 (suspended by default)...")
cur.execute("""
    INSERT OR IGNORE INTO servicios_reglas (servicio_id, regla_id, parametros_json)
    VALUES (3, ?, ?)
""", (exacto_dia_id, json.dumps({"dia_semana": "Viernes", "exacto_dias": 1, "dinamico_licencias": True, "suspendida": True})))

conn.commit()
print("Migration completed successfully!")

print("\n--- Current configuration in servicios_reglas for Service 3 (Findes / Specific Day) ---")
cur.execute("""
    SELECT sr.id, rc.codigo_regla, sr.parametros_json
    FROM servicios_reglas sr
    JOIN reglas_catalogo rc ON sr.regla_id = rc.id
    WHERE sr.servicio_id = 3 AND rc.codigo_regla IN ('MIN_FINDES_MES', 'EXACTO_FINDES_MES', 'MIN_DIA_ESPECIFICO_MES', 'EXACTO_DIA_ESPECIFICO_MES')
""")
for row in cur.fetchall():
    print(row)

conn.close()
