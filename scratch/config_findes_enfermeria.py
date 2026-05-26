"""
Configura las reglas de fines de semana para Enfermeria (servicio_id=2):
1. Agrega MIN_FINDES_MES = 1 (regla dura: al menos 1 finde por mes)
2. Sube PESO_EQUIDAD_FINDES_MENSUAL_CALENDARIO de 500 a 2000
3. Agrega PESO_EQUIDAD_FINDES_ANUAL con peso=500
"""
import sys; sys.stdout.reconfigure(encoding='utf-8')
import sqlite3
import json

conn = sqlite3.connect('cronograma_inteligente.db')
cur = conn.cursor()

SERVICIO_ID = 2

# --- 1. MIN_FINDES_MES (regla_id=179) ---
cur.execute("SELECT id FROM reglas_catalogo WHERE codigo_regla='MIN_FINDES_MES'")
row = cur.fetchone()
if not row:
    print("ERROR: No existe MIN_FINDES_MES en el catalogo")
else:
    regla_id_min_fin = row[0]
    cur.execute("SELECT id, parametros_json FROM servicios_reglas WHERE servicio_id=? AND regla_id=?",
                (SERVICIO_ID, regla_id_min_fin))
    existing = cur.fetchone()
    if existing:
        cur.execute("UPDATE servicios_reglas SET parametros_json=? WHERE id=?",
                    (json.dumps({"min_findes": 1}), existing[0]))
        print(f"[ACTUALIZADO] MIN_FINDES_MES: id={existing[0]}, min_findes=1")
    else:
        cur.execute("INSERT INTO servicios_reglas (servicio_id, regla_id, parametros_json) VALUES (?,?,?)",
                    (SERVICIO_ID, regla_id_min_fin, json.dumps({"min_findes": 1})))
        print(f"[CREADO] MIN_FINDES_MES con min_findes=1 para servicio {SERVICIO_ID}")

# --- 2. PESO_EQUIDAD_FINDES_MENSUAL_CALENDARIO (regla_id=113) -> peso 2000 ---
cur.execute("SELECT id FROM reglas_catalogo WHERE codigo_regla='PESO_EQUIDAD_FINDES_MENSUAL_CALENDARIO'")
row = cur.fetchone()
if not row:
    print("ERROR: No existe PESO_EQUIDAD_FINDES_MENSUAL_CALENDARIO en el catalogo")
else:
    regla_id_mes_cal = row[0]
    cur.execute("SELECT id, parametros_json FROM servicios_reglas WHERE servicio_id=? AND regla_id=?",
                (SERVICIO_ID, regla_id_mes_cal))
    existing = cur.fetchone()
    if existing:
        old_peso = json.loads(existing[1]).get('peso')
        cur.execute("UPDATE servicios_reglas SET parametros_json=? WHERE id=?",
                    (json.dumps({"peso": 2000}), existing[0]))
        print(f"[ACTUALIZADO] PESO_EQUIDAD_FINDES_MENSUAL_CALENDARIO: peso {old_peso} -> 2000")
    else:
        cur.execute("INSERT INTO servicios_reglas (servicio_id, regla_id, parametros_json) VALUES (?,?,?)",
                    (SERVICIO_ID, regla_id_mes_cal, json.dumps({"peso": 2000})))
        print(f"[CREADO] PESO_EQUIDAD_FINDES_MENSUAL_CALENDARIO peso=2000")

# --- 3. PESO_EQUIDAD_FINDES_ANUAL (regla_id=66) -> peso 500 ---
cur.execute("SELECT id FROM reglas_catalogo WHERE codigo_regla='PESO_EQUIDAD_FINDES_ANUAL'")
row = cur.fetchone()
if not row:
    print("ERROR: No existe PESO_EQUIDAD_FINDES_ANUAL en el catalogo")
else:
    regla_id_anual = row[0]
    cur.execute("SELECT id, parametros_json FROM servicios_reglas WHERE servicio_id=? AND regla_id=?",
                (SERVICIO_ID, regla_id_anual))
    existing = cur.fetchone()
    if existing:
        old_peso = json.loads(existing[1]).get('peso')
        cur.execute("UPDATE servicios_reglas SET parametros_json=? WHERE id=?",
                    (json.dumps({"peso": 500}), existing[0]))
        print(f"[ACTUALIZADO] PESO_EQUIDAD_FINDES_ANUAL: peso {old_peso} -> 500")
    else:
        cur.execute("INSERT INTO servicios_reglas (servicio_id, regla_id, parametros_json) VALUES (?,?,?)",
                    (SERVICIO_ID, regla_id_anual, json.dumps({"peso": 500})))
        print(f"[CREADO] PESO_EQUIDAD_FINDES_ANUAL peso=500")

conn.commit()

# Verificacion final
print("\n=== Reglas de fines de semana activas para servicio 2 ===")
cur.execute("""
    SELECT rc.codigo_regla, sr.parametros_json
    FROM servicios_reglas sr
    JOIN reglas_catalogo rc ON sr.regla_id = rc.id
    WHERE sr.servicio_id = 2
      AND rc.codigo_regla LIKE '%FINDE%'
    ORDER BY rc.codigo_regla
""")
for row in cur.fetchall():
    print(f"  {row[0]}: {row[1]}")

conn.close()
print("\nListo!")
