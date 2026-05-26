import sys; sys.stdout.reconfigure(encoding='utf-8')
import sqlite3
from datetime import date, timedelta
from collections import defaultdict

conn = sqlite3.connect('cronograma_inteligente.db')
cur = conn.cursor()

FECHA_INICIO = "2026-07-01"
FECHA_FIN    = "2026-07-31"
fecha_inicio_dt = date.fromisoformat(FECHA_INICIO)
fecha_fin_dt    = date.fromisoformat(FECHA_FIN)
dias_del_bloque = (fecha_fin_dt - fecha_inicio_dt).days + 1

FERIADOS = ["2026-07-09"]
feriados_dt = {date.fromisoformat(f) for f in FERIADOS}

# offset: julio empieza miercoles = 2
offset_dia = fecha_inicio_dt.weekday()  # 2

# Calcular dias de finde por indice
def es_finde(d):
    fecha_d = fecha_inicio_dt + timedelta(days=d)
    return fecha_d.weekday() >= 5 or fecha_d in feriados_dt

# Licencias por persona
cur.execute("SELECT nombre, fecha_inicio, fecha_fin FROM licencias WHERE fecha_inicio <= ? AND fecha_fin >= ?",
            (FECHA_FIN, FECHA_INICIO))
lic_raw = cur.fetchall()
licencias_por_persona = defaultdict(set)
for nombre, fi, ff in lic_raw:
    fi_dt = date.fromisoformat(fi)
    ff_dt = date.fromisoformat(ff)
    for d in range(dias_del_bloque):
        fecha_d = fecha_inicio_dt + timedelta(days=d)
        if fi_dt <= fecha_d <= ff_dt:
            licencias_por_persona[nombre].add(d)

# FRANCO_FORZADO por persona en julio
cur.execute("""
    SELECT pra.personal_nombre, pra.fecha_inicio, pra.fecha_fin
    FROM personal_reglas_ajustes pra
    WHERE pra.codigo_regla = 'FRANCO_FORZADO'
      AND pra.accion = 'SOBRESCRIBIR'
      AND pra.fecha_inicio <= ? AND (pra.fecha_fin >= ? OR pra.fecha_fin IS NULL)
""", (FECHA_FIN, FECHA_INICIO))
francos_raw = cur.fetchall()
francos_por_persona = defaultdict(set)
for nombre, fi, ff in francos_raw:
    fi_dt = date.fromisoformat(fi)
    ff_dt = date.fromisoformat(ff) if ff else fecha_fin_dt
    for d in range(dias_del_bloque):
        fecha_d = fecha_inicio_dt + timedelta(days=d)
        if fi_dt <= fecha_d <= ff_dt:
            francos_por_persona[nombre].add(d)

# Semanas de finde
semanas_finde = {}
for d in range(dias_del_bloque):
    if es_finde(d):
        fecha_d = fecha_inicio_dt + timedelta(days=d)
        lunes = fecha_d - timedelta(days=fecha_d.weekday())
        semanas_finde.setdefault(lunes.isoformat(), []).append(d)

# Obtener personal del servicio 2
cur.execute("SELECT nombre FROM personal WHERE servicio_id=2")
personal = [r[0] for r in cur.fetchall()]

print("Verificacion de MIN_FINDES_MES=1 para Julio 2026:")
print(f"{'Nombre':<30} {'Hab':>4} {'Vars':>5}  Riesgo")
print("-" * 50)

problemas = []
for nombre in sorted(personal):
    dias_lic = licencias_por_persona[nombre]
    dias_franco = francos_por_persona[nombre]
    bloqueados = dias_lic | dias_franco

    # Contar fines habilitados (donde al menos 1 dia de la semana esta libre)
    habiles = 0
    vars_disponibles = 0
    for lunes_iso, dias_sem in semanas_finde.items():
        dias_habilitados = [d for d in dias_sem if d not in bloqueados]
        if dias_habilitados:
            habiles += 1
            vars_disponibles += 1

    riesgo = ""
    if habiles == 0:
        riesgo = "EXENTO (0 fines habiles)"
    elif vars_disponibles >= 1:
        riesgo = "OK"
    else:
        riesgo = "!!! POTENCIAL INFEASIBLE !!!"
        problemas.append(nombre)

    if habiles < 4 or riesgo != "OK":
        print(f"{nombre:<30} {habiles:>4} {vars_disponibles:>5}  {riesgo}")

print("-" * 50)
if problemas:
    print(f"POSIBLES INFEASIBLES: {problemas}")
else:
    print("Ninguna persona deberia ser infeasible por MIN_FINDES_MES=1")
    print("(el timeout es por dificultad de busqueda, no por imposibilidad)")

conn.close()
