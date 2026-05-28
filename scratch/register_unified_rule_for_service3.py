import sqlite3
import json

db_path = "cronograma_inteligente.db"
conn = sqlite3.connect(db_path)
cur = conn.cursor()

# 1. Check if the catalog entry exists
cur.execute("SELECT id FROM reglas_catalogo WHERE codigo_regla = 'EXACTO_FINDE_Y_DIA'")
row = cur.fetchone()
if not row:
    print("Warning: EXACTO_FINDE_Y_DIA not in regras_catalogo. Inserting it first.")
    cur.execute("""
        INSERT INTO reglas_catalogo (codigo_regla, tipo, descripcion)
        VALUES ('EXACTO_FINDE_Y_DIA', 'HARD', 'Unified rule for weekends and weekday target.')
    """)
    conn.commit()

# 2. Setup rule configuration for Service 3
# Config:
# 5 available weekends -> 2 weekends, 2 fridays
# 4 available weekends -> 2 weekends, 1 fridays
# 3 available weekends -> 2 weekends, 0 fridays
# 2 available weekends -> 1 weekends, 1 fridays
# 1 available weekends -> 1 weekends, 0 fridays
# 0 available weekends -> 0 weekends, 0 fridays
params_json = {
    "dia_semana": "Viernes",
    "findes_por_disponibilidad": {
        "5": 2,
        "4": 2,
        "3": 2,
        "2": 1,
        "1": 1,
        "0": 0
    },
    "dias_por_disponibilidad": {
        "5": 2,
        "4": 1,
        "3": 0,
        "2": 1,
        "1": 0,
        "0": 0
    },
    "modo": "HARD",
    "peso_soft": 100000
}

# 3. Insert or update the rule for Service 3
cur.execute("""
    INSERT OR REPLACE INTO servicios_reglas (servicio_id, codigo_regla, parametros_json, activo)
    VALUES (3, 'EXACTO_FINDE_Y_DIA', ?, 1)
""", (json.dumps(params_json),))
print("Successfully registered and enabled EXACTO_FINDE_Y_DIA for Service 3 in HARD mode.")

# 4. Deactivate old overlapping rules for Service 3 to prevent conflicts
old_rules = ['MIN_FINDES_MES', 'EXACTO_FINDES_MES', 'MIN_DIA_ESPECIFICO_MES', 'EXACTO_DIA_ESPECIFICO_MES', 'EXACTO_DIA_ESPECIFICO_MES_HARD']
for rule in old_rules:
    cur.execute("""
        UPDATE servicios_reglas 
        SET activo = 0 
        WHERE servicio_id = 3 AND codigo_regla = ?
    """, (rule,))
    print(f"Deactivated overlapping rule '{rule}' for Service 3.")

conn.commit()
conn.close()
print("All database registrations completed successfully.")
