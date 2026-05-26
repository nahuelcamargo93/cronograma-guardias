import sys
sys.stdout.reconfigure(encoding='utf-8')
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

# Semanas del bloque (igual que soft_rules.py)
dias_por_semana_calendario = {}
for d in range(dias_del_bloque):
    fecha_d = fecha_inicio_dt + timedelta(days=d)
    lunes_semana = fecha_d - timedelta(days=fecha_d.weekday())
    sem_key = lunes_semana.isoformat()
    dias_por_semana_calendario.setdefault(sem_key, []).append(d)

# Personas con rotacion incompleta
INCOMPLETAS = ['BASCUR ALEJANDRA', 'CAMPOS PRISCILA', 'CASTRO LUCIANO',
               'ECHENIQUE ROCIO', 'GUINAZU KARINA', 'MEDINA LAURA', 'MIRANDA LUCIANA', 'VERA JULIETA']

# Obtener licencias
cur.execute("""
    SELECT nombre, fecha_inicio, fecha_fin, tipo
    FROM licencias
    WHERE fecha_inicio <= ? AND fecha_fin >= ?
""", (FECHA_FIN, FECHA_INICIO))

licencias_raw = cur.fetchall()

licencias_por_persona = defaultdict(list)
for nombre, fi, ff, tipo in licencias_raw:
    fi_dt = date.fromisoformat(fi)
    ff_dt = date.fromisoformat(ff)
    dias_lic = []
    for d in range(dias_del_bloque):
        fecha_d = fecha_inicio_dt + timedelta(days=d)
        if fi_dt <= fecha_d <= ff_dt:
            dias_lic.append(d)
    if dias_lic:
        licencias_por_persona[nombre].extend(dias_lic)

print("Analisis de personas con rotacion 3/4:")
print("="*70)
for nombre in sorted(licencias_por_persona.keys()):
    dias_lic = set(licencias_por_persona[nombre])

    semanas_disponibles = 0
    for sem_key_rot, dias_sem_rot in dias_por_semana_calendario.items():
        if len(dias_sem_rot) >= 4:
            dias_libres = [d for d in dias_sem_rot if d not in dias_lic]
            if len(dias_libres) >= 4:
                semanas_disponibles += 1

    req = min(4, semanas_disponibles)
    print(f"{nombre}: {len(dias_lic)} dias de licencia, {semanas_disponibles} semanas disponibles -> req_families={req}")

print("\nPersonas sin licencia que figuran incompletas:")
cur.execute("SELECT nombre FROM personal WHERE servicio_id=2")
todos = {r[0] for r in cur.fetchall()}
for nombre in ['BASCUR ALEJANDRA', 'CAMPOS PRISCILA', 'CASTRO LUCIANO',
               'ECHENIQUE ROCIO', 'MEDINA LAURA', 'MIRANDA LUCIANA', 'VERA JULIETA']:
    if nombre not in licencias_por_persona:
        print(f"  {nombre}: SIN licencia registrada -> req deberia ser 4 (POSIBLE BUG)")

conn.close()
