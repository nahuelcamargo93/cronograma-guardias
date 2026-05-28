"""
Diagnóstico matemático: ¿cuántas horas puede hacer cada médico con las restricciones actuales?

Objetivo: encontrar el MAX_HORAS factible que el solver puede satisfacer.
"""
import sys
sys.path.insert(0, '.')
from data import FECHA_INICIO, FECHA_FIN, SERVICIO_ID, FERIADOS
from datetime import date, timedelta

fecha_inicio_dt = date.fromisoformat(FECHA_INICIO)
fecha_fin_dt = date.fromisoformat(FECHA_FIN)
dias_del_bloque = (fecha_fin_dt - fecha_inicio_dt).days + 1

print(f"Período: {FECHA_INICIO} a {FECHA_FIN} ({dias_del_bloque} días)")

# Parámetros
DESCANSO_G = 24  # post-guardia de 24h (actualizado)
DESCANSO_D = 36  # post-turno día de 12h
DESCANSO_N = 36  # post-turno noche de 12h
N_MEDICOS = 26
MIN_HORAS = 185
MAX_HORAS = 198

# Calcular máximas guardias de 24h en 31 días con descanso 24h:
# Patrón: Trabaja día D → libre día D+1 → trabaja día D+2 → ...
# = trabaja cada 2 días = 31/2 = 15.5 → 15 guardias × 24h = 360h
# Pero MAX_HORAS=198 limita a 198/24 = 8.25 → máx 8 guardias × 24h = 192h

# Con descanso 24h post-G(24h):
max_guardias_g = dias_del_bloque // 2  # sin contar MAX_HORAS
max_horas_solo_g = max_guardias_g * 24
print(f"\nCon G_Planta(24h) + descanso 24h:")
print(f"  Max guardias en {dias_del_bloque} días: {max_guardias_g}")
print(f"  Max horas: {max_horas_solo_g}h")
print(f"  Limitado por MAX_HORAS ({MAX_HORAS}h): {MAX_HORAS // 24} guardias = {(MAX_HORAS // 24) * 24}h")
print(f"  Min necesario ({MIN_HORAS}h): {MIN_HORAS / 24:.1f} guardias = {MIN_HORAS}h -> {(MIN_HORAS + 23) // 24} guardias = {((MIN_HORAS + 23) // 24) * 24}h")

print(f"\n=== ANÁLISIS DE COBERTURA ===")
print(f"Médicos planta: {N_MEDICOS}")

# Demanda actual: 3 planta en guardia 24h
DEMANDA_G_ACTUAL = 3  # min guardias simultáneas
DEMANDA_G_MAX = 5

# Horas de guardia totales en el mes (con demanda de 3):
horas_guardias_totales = dias_del_bloque * DEMANDA_G_ACTUAL * 24
print(f"\nCon demanda {DEMANDA_G_ACTUAL} médicos en guardia 24h todo el mes:")
print(f"  Horas totales de guardia: {horas_guardias_totales}h")
print(f"  Horas por médico (si se reparte equitativamente): {horas_guardias_totales/N_MEDICOS:.1f}h")
print(f"  ¿Factible con MIN_HORAS={MIN_HORAS}h? {'NO' if horas_guardias_totales/N_MEDICOS < MIN_HORAS else 'SI'}")

# Demanda de 6 médicos en guardia de 24h:
DEMANDA_G_6 = 6
horas_guardias_totales_6 = dias_del_bloque * DEMANDA_G_6 * 24
print(f"\nCon demanda {DEMANDA_G_6} médicos en guardia 24h todo el mes:")
print(f"  Horas totales de guardia: {horas_guardias_totales_6}h")
print(f"  Horas por médico: {horas_guardias_totales_6/N_MEDICOS:.1f}h")
print(f"  ¿Factible con MIN_HORAS={MIN_HORAS}h? {'NO' if horas_guardias_totales_6/N_MEDICOS < MIN_HORAS else 'SI'}")
print(f"  ¿Factible con MAX_HORAS={MAX_HORAS}h? {'NO' if horas_guardias_totales_6/N_MEDICOS > MAX_HORAS else 'SI'}")

# ¿Qué demanda necesitamos para que MIN_HORAS sea factible?
demanda_necesaria = (N_MEDICOS * MIN_HORAS) / (dias_del_bloque * 24)
print(f"\nDemanda necesaria para que MIN_HORAS={MIN_HORAS}h sea factible:")
print(f"  {N_MEDICOS} * {MIN_HORAS} / ({dias_del_bloque} * 24) = {demanda_necesaria:.2f} médicos simultáneos")
print(f"  -> Redondeado: {round(demanda_necesaria)} médicos en guardia de 24h por día")

# ¿Qué MIN_HORAS es factible con demanda de 3?
min_factible_demanda3 = horas_guardias_totales / N_MEDICOS
print(f"\nMIN_HORAS factible con demanda=3: {min_factible_demanda3:.0f}h")
min_factible_demanda6 = horas_guardias_totales_6 / N_MEDICOS
print(f"MIN_HORAS factible con demanda=6: {min_factible_demanda6:.0f}h")

print(f"\n=== RECOMENDACIÓN ===")
if min_factible_demanda3 < MIN_HORAS:
    print(f"PROBLEMA: Con demanda=3 médicos/guardia, el MIN_HORAS máximo alcanzable es {min_factible_demanda3:.0f}h")
    print(f"  Opciones:")
    print(f"  A) Reducir MIN_HORAS de {MIN_HORAS}h a ~{int(min_factible_demanda3)}h (o menos)")
    print(f"  B) Aumentar demanda de 3 a {round(demanda_necesaria)} médicos en guardia")
    print(f"  C) Mezcla: demanda=6 médicos → MIN_HORAS factible = {int(min_factible_demanda6)}h")
