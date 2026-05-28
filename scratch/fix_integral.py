"""
Fix integral para imposibilidad matemática en Servicio 3:

1. Subir cantidad_max de 5 a 6 en demanda_config
2. Bajar MIN_HORAS_MES_CALENDARIO de 185h a 168h 
3. Agregar PESO_BRECHA_DIARIA_PERSONAL como soft rule para equidad diaria

Fundamento:
  - 26 médicos con max=6 por día: 6×31×24÷26 = 171.7h promedio
  - Con MIN_HORAS=168h (7 guardias de 24h): factible ✓
  - PESO_BRECHA_DIARIA_PERSONAL penaliza diferencias de cobertura entre días
"""
import sqlite3, json

con = sqlite3.connect('cronograma_inteligente.db')
cur = con.cursor()

print("=== ESTADO ACTUAL ===")
cur.execute("""
    SELECT dc.tipo_dia, dc.hora_inicio, dc.hora_fin, dc.cantidad_min, dc.cantidad_max, pu.nombre
    FROM demanda_config dc
    JOIN puestos pu ON dc.puesto_id = pu.id
    WHERE pu.servicio_id = 3
    ORDER BY dc.tipo_dia, dc.hora_inicio
""")
for r in cur.fetchall():
    print(f"  [{r[0]}] {r[1]}-{r[2]}: {r[5]} min={r[3]}, max={r[4]}")

cur.execute("SELECT parametros_json FROM servicios_reglas WHERE servicio_id=3 AND codigo_regla='MIN_HORAS_MES_CALENDARIO'")
row = cur.fetchone()
print(f"\nMIN_HORAS_MES_CALENDARIO: {row[0] if row else 'NO ENCONTRADA'}")

# === FIX 1: Subir cantidad_max de 5 a 6 en demanda_config para Servicio 3 ===
print("\n=== FIX 1: Subir cantidad_max de 5 a 6 ===")
cur.execute("""
    SELECT dc.id, dc.tipo_dia, dc.hora_inicio, dc.cantidad_min, dc.cantidad_max, pu.nombre
    FROM demanda_config dc
    JOIN puestos pu ON dc.puesto_id = pu.id
    WHERE pu.servicio_id = 3 AND dc.cantidad_max = 5
""")
rows_to_update = cur.fetchall()
for row in rows_to_update:
    cur.execute("UPDATE demanda_config SET cantidad_max = 6 WHERE id = ?", (row[0],))
    print(f"  [{row[1]}] {row[2]}: {row[5]} max: 5 -> 6")

# === FIX 2: Bajar MIN_HORAS de 185h a 168h ===
print("\n=== FIX 2: Bajar MIN_HORAS de 185h a 168h ===")
cur.execute("SELECT parametros_json FROM servicios_reglas WHERE servicio_id=3 AND codigo_regla='MIN_HORAS_MES_CALENDARIO'")
row = cur.fetchone()
if row:
    params = json.loads(row[0])
    old_min = params.get('min_horas', '?')
    params['min_horas'] = 168
    new_json = json.dumps(params, ensure_ascii=False)
    cur.execute(
        "UPDATE servicios_reglas SET parametros_json=? WHERE servicio_id=3 AND codigo_regla='MIN_HORAS_MES_CALENDARIO'",
        (new_json,)
    )
    print(f"  MIN_HORAS: {old_min}h -> 168h")
else:
    cur.execute(
        "INSERT OR IGNORE INTO servicios_reglas (servicio_id, codigo_regla, parametros_json, activo) VALUES (3, 'MIN_HORAS_MES_CALENDARIO', ?, 1)",
        (json.dumps({"min_horas": 168}),)
    )
    print("  Creado MIN_HORAS_MES_CALENDARIO=168h")

# === FIX 3: Agregar PESO_BRECHA_DIARIA_PERSONAL para equidad ===
print("\n=== FIX 3: Agregar PESO_BRECHA_DIARIA_PERSONAL ===")
# Verificar si ya existe en el catálogo
cur.execute("SELECT codigo_regla FROM reglas_catalogo WHERE codigo_regla='PESO_BRECHA_DIARIA_PERSONAL'")
if not cur.fetchone():
    cur.execute("""
        INSERT OR IGNORE INTO reglas_catalogo (codigo_regla, tipo, descripcion)
        VALUES ('PESO_BRECHA_DIARIA_PERSONAL', 'SOFT', 
                'Penaliza la diferencia de personal asignado entre dias para evitar desequilibrios (un dia 6 y otro dia 3). JSON: {\"peso\": 5000}')
    """)
    print("  Creado PESO_BRECHA_DIARIA_PERSONAL en catalogo")

# Verificar si ya está en servicios_reglas para servicio 3
cur.execute("SELECT parametros_json FROM servicios_reglas WHERE servicio_id=3 AND codigo_regla='PESO_BRECHA_DIARIA_PERSONAL'")
row_eq = cur.fetchone()
if not row_eq:
    cur.execute("""
        INSERT OR IGNORE INTO servicios_reglas (servicio_id, codigo_regla, parametros_json, activo)
        VALUES (3, 'PESO_BRECHA_DIARIA_PERSONAL', '{"peso": 5000}', 1)
    """)
    print("  Agregado PESO_BRECHA_DIARIA_PERSONAL (peso=5000) al Servicio 3")
else:
    print(f"  Ya existe: {row_eq[0]}")

con.commit()

print("\n=== VERIFICACIÓN FINAL ===")
cur.execute("""
    SELECT dc.tipo_dia, dc.hora_inicio, dc.hora_fin, dc.cantidad_min, dc.cantidad_max, pu.nombre
    FROM demanda_config dc
    JOIN puestos pu ON dc.puesto_id = pu.id
    WHERE pu.servicio_id = 3
    ORDER BY dc.tipo_dia, dc.hora_inicio
""")
for r in cur.fetchall():
    print(f"  [{r[0]}] {r[1]}-{r[2]}: {r[5]} min={r[3]}, max={r[4]}")

cur.execute("SELECT parametros_json FROM servicios_reglas WHERE servicio_id=3 AND codigo_regla='MIN_HORAS_MES_CALENDARIO'")
print(f"\nMIN_HORAS_MES_CALENDARIO: {cur.fetchone()[0]}")
cur.execute("SELECT parametros_json FROM servicios_reglas WHERE servicio_id=3 AND codigo_regla='DESCANSO_ENTRE_TURNOS'")
print(f"DESCANSO_ENTRE_TURNOS: {cur.fetchone()[0]}")

print("\n=== CALCULO MATEMATICO ===")
n_medicos = 26
max_demand = 6
dias = 31
horas_turno_g = 24
promedio = (max_demand * dias * horas_turno_g) / n_medicos
print(f"Con max={max_demand} y {n_medicos} medicos: promedio = {promedio:.1f}h/medico")
print(f"MIN_HORAS=168h factible? {'SI' if promedio >= 168 else 'NO'}")
print(f"MAX_HORAS=198h respetado? {'SI - hay margen' if promedio < 198 else 'AJUSTADO'}")

con.close()
print("\nEjecuta: python main.py")
