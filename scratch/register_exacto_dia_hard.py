"""
Registra EXACTO_DIA_ESPECIFICO_MES_HARD en el catálogo de reglas
y la activa para el servicio 3 con los mismos parámetros que la versión soft.
"""
import sqlite3
import json

conn = sqlite3.connect('cronograma_inteligente.db')
cur = conn.cursor()

# 1. Verificar si ya existe en el catálogo
cur.execute("SELECT id FROM reglas_catalogo WHERE codigo_regla = 'EXACTO_DIA_ESPECIFICO_MES_HARD'")
row = cur.fetchone()
if row:
    print(f"[OK] Ya existe en catálogo con id={row[0]}")
else:
    cur.execute("""
        INSERT INTO reglas_catalogo (codigo_regla, tipo, descripcion)
        VALUES ('EXACTO_DIA_ESPECIFICO_MES_HARD', 'HARD',
                'Restriccion DURA: el personal trabaja exactamente N veces un dia especifico en el mes. No violable. JSON: {"dia_semana": "Viernes", "exacto_dias": 1, "dinamico_licencias": true}')
    """)
    print(f"[OK] Insertada en catálogo con id={cur.lastrowid}")

# 2. Verificar si ya existe para el servicio 3
cur.execute("SELECT id, activo FROM servicios_reglas WHERE servicio_id = 3 AND codigo_regla = 'EXACTO_DIA_ESPECIFICO_MES_HARD'")
row = cur.fetchone()

# Obtener parámetros de la versión soft para copiarlos
cur.execute("SELECT parametros_json FROM servicios_reglas WHERE servicio_id = 3 AND codigo_regla = 'EXACTO_DIA_ESPECIFICO_MES'")
soft_params = cur.fetchone()
params_json = soft_params[0] if soft_params else '{"dia_semana": "Viernes", "exacto_dias": 1, "dinamico_licencias": true}'

print(f"Parámetros copiados de soft: {params_json}")

if row:
    print(f"[OK] Ya existe para servicio 3 (id={row[0]}, activo={row[1]})")
    if not row[1]:
        cur.execute("UPDATE servicios_reglas SET activo = 1 WHERE id = ?", (row[0],))
        print("[OK] Activada")
else:
    cur.execute("""
        INSERT INTO servicios_reglas (servicio_id, codigo_regla, parametros_json, activo)
        VALUES (3, 'EXACTO_DIA_ESPECIFICO_MES_HARD', ?, 1)
    """, (params_json,))
    print(f"[OK] Insertada para servicio 3 con id={cur.lastrowid}")

conn.commit()

# 3. Verificar estado final
cur.execute("SELECT id, codigo_regla, parametros_json, activo FROM servicios_reglas WHERE servicio_id = 3 AND codigo_regla LIKE '%DIA_ESPECIFICO%'")
print("\n=== Estado final reglas DIA_ESPECIFICO para servicio 3 ===")
for r in cur.fetchall():
    print(r)

conn.close()
print("\nListo.")
