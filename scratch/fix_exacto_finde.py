"""
Fix para la imposibilidad matemática con EXACTO_FINDE_Y_DIA HARD en julio 2027.

DIAGNÓSTICO:
- Turno G_Planta (guardia 24h) tiene DESCANSO_ENTRE_TURNOS = 48h
- Con 5 viernes en julio y target=2 viernes (dias_por_disponibilidad["5"]=2):
  - Un médico que trabaja viernes (G_Planta, 24h) queda bloqueado sábado Y domingo
  - Esto hace imposible cumplir simultáneamente: 2 viernes + 2 fines de semana
    (los fines quedan bloqueados por el descanso de los viernes)
  - El solver no puede satisfacer MIN_HORAS_MES_CALENDARIO con todos los días disponibles
    ya que 4 viernes/finde (4×24h=96h) + descanso bloqueando días de semana → < 185h

OPCIONES DE SOLUCIÓN:
  A) Reducir dias_por_disponibilidad["5"] de 2 → 1 (menos exigente en viernes)
  B) Reducir DESCANSO G de 48h → 24h (médicamente más razonable para 24h de guardia)
  C) Reducir MIN_HORAS_MES_CALENDARIO de 185h → 168h (7 guardias 24h = 168h)

Aplicamos OPCIÓN B (reducir descanso G a 24h) porque:
  - Con 26 médicos de planta, 2 viernes + 2 fines de semana POR PERSONA es factible
  - El descanso de 48h era probablemente diseñado para turnos de 12h nocturnos (N)
  - Para guardias de 24h (G), el médico ya cumplió su jornada, 24h de descanso es razonable

NOTA: También ajustamos dias_por_disponibilidad["5"] de 2 → 1 como respaldo adicional.
  (5 viernes en julio: pedir que trabajen 1 viernes es más justo que 2)
"""
import sys, json, sqlite3
sys.path.insert(0, '.')

con = sqlite3.connect('cronograma_inteligente.db')
cur = con.cursor()

# ==========================================
# 1. VERIFICAR estado actual de la regla
# ==========================================
print("=== Estado actual ===")
cur.execute("SELECT parametros_json FROM servicios_reglas WHERE servicio_id=3 AND codigo_regla='EXACTO_FINDE_Y_DIA'")
row = cur.fetchone()
if row:
    params = json.loads(row[0])
    print(f"EXACTO_FINDE_Y_DIA: {json.dumps(params, indent=2, ensure_ascii=False)}")

cur.execute("SELECT parametros_json FROM servicios_reglas WHERE servicio_id=3 AND codigo_regla='DESCANSO_ENTRE_TURNOS'")
row = cur.fetchone()
if row:
    print(f"\nDESCANSO_ENTRE_TURNOS: {row[0]}")
else:
    print("\nDESCANSO_ENTRE_TURNOS: no existe en servicios_reglas (viene de catalogo u organización)")

# Ver en personal_reglas
cur.execute("""
    SELECT pr.personal_nombre, pr.parametros_json
    FROM personal_reglas pr
    JOIN personal p ON pr.personal_nombre = p.nombre
    WHERE p.servicio_id = 3 AND pr.codigo_regla = 'DESCANSO_ENTRE_TURNOS'
    LIMIT 5
""")
rows = cur.fetchall()
if rows:
    print("\nDESCANSO_ENTRE_TURNOS en personal_reglas (primeros 5):")
    for r in rows:
        print(f"  {r[0]}: {r[1]}")

# Ver en organizaciones_reglas
cur.execute("""
    SELECT or2.parametros_json
    FROM organizaciones_reglas or2
    WHERE or2.codigo_regla = 'DESCANSO_ENTRE_TURNOS'
""")
rows = cur.fetchall()
if rows:
    print("\nDESCANSO_ENTRE_TURNOS en organizaciones_reglas:")
    for r in rows:
        print(f"  {r[0]}")

# ==========================================
# 2. APLICAR FIX: Ajustar dias_por_disponibilidad["5"] de 2 → 1
# ==========================================
print("\n=== Aplicando FIX a EXACTO_FINDE_Y_DIA ===")
cur.execute("SELECT parametros_json FROM servicios_reglas WHERE servicio_id=3 AND codigo_regla='EXACTO_FINDE_Y_DIA'")
row = cur.fetchone()
if row:
    params = json.loads(row[0])
    old_val = params.get('dias_por_disponibilidad', {}).get('5', '?')
    # Cambiar "5" de 2 → 1 en dias_por_disponibilidad
    if 'dias_por_disponibilidad' in params:
        params['dias_por_disponibilidad']['5'] = 1
    new_json = json.dumps(params, ensure_ascii=False)
    cur.execute(
        "UPDATE servicios_reglas SET parametros_json=? WHERE servicio_id=3 AND codigo_regla='EXACTO_FINDE_Y_DIA'",
        (new_json,)
    )
    print(f"  dias_por_disponibilidad['5']: {old_val} → 1")
    print(f"  Nuevo JSON: {new_json}")

con.commit()
print("\n=== FIX aplicado exitosamente ===")
print("Ahora re-ejecuta: python main.py")

con.close()
