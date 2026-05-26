import sys; sys.stdout.reconfigure(encoding='utf-8')
import sqlite3
from datetime import date, timedelta
from collections import defaultdict

conn = sqlite3.connect('cronograma_inteligente.db')
cur = conn.cursor()

CRONOGRAMA_ID = 122
FECHA_INICIO = "2026-07-01"
FECHA_FIN    = "2026-07-31"
fecha_inicio_dt = date.fromisoformat(FECHA_INICIO)
fecha_fin_dt    = date.fromisoformat(FECHA_FIN)
dias_del_bloque = (fecha_fin_dt - fecha_inicio_dt).days + 1

# Feriados en julio
FERIADOS = ["2026-07-09"]
feriados_dt = {date.fromisoformat(f) for f in FERIADOS}

# Todas las guardias
cur.execute("SELECT nombre, fecha, turno FROM guardias WHERE cronograma_id=? ORDER BY nombre, fecha", (CRONOGRAMA_ID,))
guardias = cur.fetchall()

por_persona = defaultdict(list)
for nombre, fecha, turno in guardias:
    por_persona[nombre].append((date.fromisoformat(fecha), turno))

# Para cada persona: calcular fines de semana habiles y trabajados
print(f"Nivelacion de fines de semana - Julio 2026 (Cronograma {CRONOGRAMA_ID})")
print(f"{'Nombre':<30} {'F.Hab':>6} {'F.Trab':>7} {'Ratio%':>7} {'FS%':>6}")
print("-" * 60)

resultados = []
for nombre in sorted(por_persona.keys()):
    guardias_p = por_persona[nombre]
    fechas_guardias = {f for f, t in guardias_p}
    
    # Identificar fines de semana del mes (agrupados por semana)
    semanas_finde = {}  # lunes_iso -> [sabado, domingo]
    for d in range(dias_del_bloque):
        fecha_d = fecha_inicio_dt + timedelta(days=d)
        dow = fecha_d.weekday()  # 5=Sabado, 6=Domingo
        if dow >= 5 or fecha_d in feriados_dt:
            lunes = fecha_d - timedelta(days=fecha_d.weekday())
            semanas_finde.setdefault(lunes, []).append(fecha_d)
    
    # Semanas donde hay al menos un dia de fin de semana (S o D, no feriado entre semana)
    semanas_finde_puro = {lunes: dias for lunes, dias in semanas_finde.items()
                          if any(d.weekday() >= 5 for d in dias)}
    
    # Licencias del empleado
    cur.execute("SELECT fecha_inicio, fecha_fin FROM licencias WHERE nombre=?", (nombre,))
    licencias = [(date.fromisoformat(fi), date.fromisoformat(ff)) for fi, ff in cur.fetchall()]
    
    def tiene_licencia(fecha_d):
        for fi, ff in licencias:
            if fi <= fecha_d <= ff:
                return True
        return False
    
    # Fines habiles: donde S y D no tienen licencia
    habiles = 0
    trabajados = 0
    for lunes, dias in sorted(semanas_finde_puro.items()):
        sab = lunes + timedelta(days=5)
        dom = lunes + timedelta(days=6)
        # Filtrar al rango del bloque
        sab_en_bloque = (fecha_inicio_dt <= sab <= fecha_fin_dt)
        dom_en_bloque = (fecha_inicio_dt <= dom <= fecha_fin_dt)
        
        if not sab_en_bloque and not dom_en_bloque:
            continue
        
        sab_ok = (not sab_en_bloque) or not tiene_licencia(sab)
        dom_ok = (not dom_en_bloque) or not tiene_licencia(dom)
        
        if sab_ok or dom_ok:
            habiles += 1
            # Trabaja si tiene guardia en S o D
            trabaja = (sab_en_bloque and sab in fechas_guardias) or (dom_en_bloque and dom in fechas_guardias)
            if trabaja:
                trabajados += 1
    
    ratio = round(100 * trabajados / habiles) if habiles > 0 else 0
    resultados.append((nombre, habiles, trabajados, ratio))
    print(f"{nombre:<30} {habiles:>6} {trabajados:>7} {ratio:>6}%")

# Estadisticas
ratios = [r[3] for r in resultados if r[1] > 0]
if ratios:
    print("-" * 60)
    print(f"{'MIN':>30} {min(r[1] for r in resultados):>6} {min(r[2] for r in resultados):>7} {min(ratios):>6}%")
    print(f"{'MAX':>30} {max(r[1] for r in resultados):>6} {max(r[2] for r in resultados):>7} {max(ratios):>6}%")
    print(f"{'SPREAD (max-min ratio)':>30}                     {max(ratios)-min(ratios):>5}%")

conn.close()
