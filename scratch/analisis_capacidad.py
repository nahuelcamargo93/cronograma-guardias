"""
Diagnóstico de capacidad mensual para servicio 3 con EXACTO_FINDE_Y_DIA HARD.
Julio 2027: 31 días.
- 5 fines de semana (Sáb+Dom): 5, 12, 13, 19, 20, 26, 27 julio
- 5 viernes: 4, 11, 18, 25 julio (¿4 o 5 viernes?)
"""
from datetime import date, timedelta

fecha_inicio = date(2027, 7, 1)
fecha_fin = date(2027, 7, 31)
dias = 31

# Clasificar días
viernes = []
finde = []  # Sab+Dom
semana = []  # Lun-Jue

for i in range(dias):
    d = fecha_inicio + timedelta(days=i)
    wd = d.weekday()  # 0=Lun, 4=Vie, 5=Sab, 6=Dom
    if wd == 4:
        viernes.append(i)
    elif wd in (5, 6):
        finde.append(i)
    else:
        semana.append(i)  # Lun-Jue

print(f"Julio 2027: {dias} días")
print(f"Viernes: {len(viernes)} días - índices {viernes}")
print(f"Finde (Sáb+Dom): {len(finde)} días - índices {finde}")
print(f"Semana (Lun-Jue): {len(semana)} días - índices {semana}")

# Con EXACTO_FINDE_Y_DIA HARD, k=5 fines de semana, k_dia=4 viernes
# (Julio 2027 tiene 4 viernes: 4, 11, 18, 25)
k_finde = 5  # grupos de fin de semana (4 completos + 1 dia)
k_via = 4   # viernes

# Target según la DB:
# finds_por_disponibilidad: {"5": 2, ...}
# dias_por_disponibilidad: {"5": 2, "4": 1, ...}
# k_finde = hay que contar grupos de sabado-domingo
import sqlite3, json
con = sqlite3.connect('cronograma_inteligente.db')
cur = con.cursor()
cur.execute("SELECT parametros_json FROM servicios_reglas WHERE servicio_id=3 AND codigo_regla='EXACTO_FINDE_Y_DIA'")
row = cur.fetchone()
params = json.loads(row[0])
con.close()

# Contar fines de semana como grupos
finde_groups = {}
for i in range(dias):
    d = fecha_inicio + timedelta(days=i)
    wd = d.weekday()
    if wd in (5, 6):
        lunes = (d - timedelta(days=d.weekday())).isoformat()
        finde_groups.setdefault(lunes, []).append(i)

k_groups = len(finde_groups)
print(f"\nGrupos de fin de semana: {k_groups}")
for lunes, dias_f in finde_groups.items():
    print(f"  Semana del {lunes}: días {dias_f} ({[(fecha_inicio+timedelta(days=d)).strftime('%a %d') for d in dias_f]})")

mapping_f = params.get('findes_por_disponibilidad', {})
mapping_d = params.get('dias_por_disponibilidad', {})

target_f = mapping_f.get(str(k_groups), 0)
target_d = mapping_d.get(str(len(viernes)), 0)

print(f"\nTarget fines de semana (k={k_groups}): {target_f}")
print(f"Target viernes (k_dia={len(viernes)}): {target_d}")

# Calcular horas mínimas con guardia de 24h
horas_finde_guardias = target_f * 24  # 1 guardia de 24h por fin de semana trabajado
horas_viernes_guardias = target_d * 24  # 1 guardia de 24h por viernes trabajado

print(f"\nHoras obligadas por finde: {horas_finde_guardias}h")
print(f"Horas obligadas por viernes: {horas_viernes_guardias}h")
print(f"Total horas obligadas por EXACTO_FINDE_Y_DIA: {horas_finde_guardias + horas_viernes_guardias}h")

min_horas = 185
max_horas = 198
print(f"\nMIN_HORAS_MES: {min_horas}h")
print(f"MAX_HORAS_MES: {max_horas}h")

horas_obligadas = horas_finde_guardias + horas_viernes_guardias
horas_adicionales_necesarias = min_horas - horas_obligadas
print(f"Horas adicionales necesarias en semana (Lun-Jue): {horas_adicionales_necesarias}h")

# ¿Cuántas guardias de 24h en semana (Lun-Jue) necesita?
# Con descanso de 24h después de cada guardia de 24h, una guardia de 24h = ocupa 2 días
print(f"\nDías Lun-Jue disponibles: {len(semana)}")

# Si una guardia de 24h requiere 48h de descanso, ocupa 3 días (el día + 2 de descanso)
# Si requiere 24h de descanso, ocupa 2 días (el día + 1 de descanso)
# Estimación de máx guardias posibles en semana (Lun-Jue) sin restricción de descanso:
guardias_sem_24h = horas_adicionales_necesarias / 24
print(f"Guardias de 24h necesarias en semana: {guardias_sem_24h:.1f}")
print(f"  Equivale a {guardias_sem_24h*2:.0f} días ocupados (con 24h descanso)")
print(f"  O {guardias_sem_24h*3:.0f} días ocupados (con 48h descanso)")
print(f"  Días Lun-Jue disponibles: {len(semana)}")

# Calcular si es posible: días disponibles - días de descanso obligatorio por finde/viernes
# Finde: una guardia de 24h el sábado -> no puede trabajar domingo. ¿O puede?
# Si trabaja el finde completo: sábado O domingo (1 guardia de 24h)
# Con descanso: necesita 24h después del domingo -> lunes libre

horas_max_semana = 12 * len(semana)  # máx 12h por turno en semana (turnos D o N)
horas_max_semana_24 = 24 * len(semana) / 2  # máx con guardias de 24h (ocupan 2 días)
print(f"\nCon turnos de 12h (D o N): máx {horas_max_semana}h en {len(semana)} días Lun-Jue")
print(f"Con turnos de 24h: máx ~{horas_max_semana_24:.0f}h (cada guardia usa 2 días)")

print(f"\n=== CONCLUSIÓN ===")
# Un médico tiene {horas_obligadas}h de fin de semana y necesita {min_horas - horas_obligadas}h más
# En semana tiene {len(semana)} días (Lun-Jue)
# Con 12h por día: puede hacer {horas_max_semana / 12:.0f} guardias -> {horas_max_semana}h
# Con 24h por 2 días: puede hacer {len(semana)//2} guardias -> {(len(semana)//2)*24}h
dias_libres_semana = len(semana) - (target_f * 1)  # después de finde trabajado, lunes libre
print(f"La restricción es FACTIBLE si {horas_max_semana}h >= {horas_adicionales_necesarias}h: {horas_max_semana >= horas_adicionales_necesarias}")
