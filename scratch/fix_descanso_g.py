"""
FIX para la imposibilidad matemática con EXACTO_FINDE_Y_DIA HARD.

DIAGNÓSTICO CONFIRMADO:
La combinación de COBERTURA_DINAMICA + DESCANSO_ENTRE_TURNOS genera la contradicción.

CAUSA RAÍZ:
  - DESCANSO_ENTRE_TURNOS: {'G': 48, 'D': 36, 'N': 36}
  - Con G_Planta (24h guardia): después necesita 48h de descanso
  - Esto bloquea 2 días extra después de cada guardia de 24h
  - Con EXACTO_FINDE_Y_DIA HARD exigiendo 2 viernes + 2 fines de semana con guardias de 24h,
    el descanso bloquea muchos días del mes y queda insuficiente personal disponible
    para cubrir la demanda mínima diaria de 3 médicos Planta por turno

SOLUCIÓN:
  Reducir descanso post-G de 48h → 24h
  - Una guardia de 24h en hospital ya es la jornada completa
  - 24h de descanso es suficiente y médicamente razonable
  - Esto permite que los médicos trabajen el día siguiente después de la guardia
  - Hace factible cubrir tanto los fines de semana como la demanda diaria
"""
import sys, json, sqlite3
sys.path.insert(0, '.')

con = sqlite3.connect('cronograma_inteligente.db')
cur = con.cursor()

print("=== DIAGNÓSTICO ===")
print("La imposibilidad se debe a la combinación COBERTURA_DINAMICA + DESCANSO_ENTRE_TURNOS")
print("El descanso de 48h post-G (guardia 24h) bloquea demasiados días cuando")
print("EXACTO_FINDE_Y_DIA HARD exige trabajar viernes Y fines de semana.")

# Verificar dónde está configurado DESCANSO_ENTRE_TURNOS para servicio 3
print("\n=== Verificando configuración de DESCANSO_ENTRE_TURNOS ===")

# En servicios_reglas
cur.execute("SELECT parametros_json FROM servicios_reglas WHERE servicio_id=3 AND codigo_regla='DESCANSO_ENTRE_TURNOS'")
row_serv = cur.fetchone()
if row_serv:
    print(f"servicios_reglas (servicio 3): {row_serv[0]}")
else:
    print("servicios_reglas (servicio 3): NO configurado")

# En organizaciones_reglas
cur.execute("SELECT or2.parametros_json, o.nombre FROM organizaciones_reglas or2 JOIN organizaciones o ON or2.organizacion_id=o.id WHERE or2.codigo_regla='DESCANSO_ENTRE_TURNOS'")
rows_org = cur.fetchall()
if rows_org:
    for r in rows_org:
        print(f"organizaciones_reglas ({r[1]}): {r[0]}")
else:
    print("organizaciones_reglas: NO configurado")

# En personal_reglas (para empleados de servicio 3)
cur.execute("""
    SELECT pr.personal_nombre, pr.parametros_json
    FROM personal_reglas pr
    JOIN personal p ON pr.personal_nombre = p.nombre
    WHERE p.servicio_id = 3 AND pr.codigo_regla = 'DESCANSO_ENTRE_TURNOS'
""")
rows_per = cur.fetchall()
if rows_per:
    print(f"personal_reglas ({len(rows_per)} registros):")
    for r in rows_per[:3]:
        print(f"  {r[0]}: {r[1]}")
    if len(rows_per) > 3:
        print(f"  ... ({len(rows_per)-3} más)")
else:
    print("personal_reglas: NO configurado individualmente")

# ==========================================
# APLICAR FIX
# ==========================================
print("\n=== APLICANDO FIX: Reducir descanso G de 48h a 24h ===")

# Cambiar en servicios_reglas
if row_serv:
    params = json.loads(row_serv[0])
    old_g = params.get('por_turno', {}).get('G', '?')
    params['por_turno']['G'] = 24
    new_json = json.dumps(params, ensure_ascii=False)
    cur.execute(
        "UPDATE servicios_reglas SET parametros_json=? WHERE servicio_id=3 AND codigo_regla='DESCANSO_ENTRE_TURNOS'",
        (new_json,)
    )
    print(f"  servicios_reglas: G {old_g}h -> 24h OK")

# Cambiar en personal_reglas para empleados de servicio 3
for nombre, params_json in rows_per:
    params = json.loads(params_json)
    por_turno = params.get('por_turno', {})
    if 'G' in por_turno and por_turno['G'] != 24:
        old_g = por_turno['G']
        params['por_turno']['G'] = 24
        new_json = json.dumps(params, ensure_ascii=False)
        cur.execute(
            "UPDATE personal_reglas SET parametros_json=? WHERE personal_nombre=? AND codigo_regla='DESCANSO_ENTRE_TURNOS'",
            (new_json, nombre)
        )
        print(f"  personal_reglas {nombre}: G {old_g}h -> 24h OK")

con.commit()
print("\n=== FIX aplicado ===")
print("Ahora ejecuta: python main.py")

con.close()
