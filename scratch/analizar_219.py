"""
Analiza el último cronograma verificando viernes y fines de semana por persona.
Tabla: guardias (cronograma_id, nombre, fecha, turno, horas, es_finde)
"""
import sqlite3
from datetime import date, timedelta
from collections import defaultdict

conn = sqlite3.connect('cronograma_inteligente.db')
cur = conn.cursor()

# Ultimo cronograma
cur.execute('SELECT id, fecha_inicio, fecha_fin, notas FROM cronogramas ORDER BY id DESC LIMIT 1')
crono = cur.fetchone()
crono_id, fecha_ini_str, fecha_fin_str, notas = crono
print(f"=== Cronograma ID {crono_id} ({fecha_ini_str} a {fecha_fin_str}) ===")
print(f"    Notas: {notas}\n")

# Traer todas las guardias del cronograma
cur.execute('SELECT nombre, fecha, turno FROM guardias WHERE cronograma_id = ? ORDER BY nombre, fecha', (crono_id,))
rows = cur.fetchall()
conn.close()

# Agrupar por persona
por_persona = defaultdict(list)
for nombre, fecha, turno in rows:
    d = date.fromisoformat(fecha)
    por_persona[nombre].append((d, turno))

DIA_NAMES = ['Lun','Mar','Mié','Jue','Vie','Sáb','Dom']

print(f"{'Nombre':<45} {'Viernes':>8} {'Fin Semanas':>12} {'Total':>7}")
print("-"*78)

for nombre in sorted(por_persona.keys()):
    dias = por_persona[nombre]
    viernes = [d for d, t in dias if d.weekday() == 4]
    finde_dias = [d for d, t in dias if d.weekday() >= 5]
    # Fines de semana por semana (una semana = un fin de semana)
    semanas_finde = set()
    for d in finde_dias:
        lunes = d - timedelta(days=d.weekday())
        semanas_finde.add(lunes)
    
    flag = ""
    if len(viernes) != 1:
        flag = "  *** VIERNES != 1 ***"
    if len(semanas_finde) != 2:
        flag += f"  *** FINDE != 2 ***"
    
    print(f"{nombre:<45} {len(viernes):>8} {len(semanas_finde):>12} {len(dias):>7}{flag}")

print("\n=== DETALLE COMPLETO DE PERSONAS CON VIERNES != 1 ===")
for nombre in sorted(por_persona.keys()):
    dias = por_persona[nombre]
    viernes = [d for d, t in dias if d.weekday() == 4]
    if len(viernes) != 1:
        print(f"\n{nombre}: tiene {len(viernes)} viernes")
        for d, t in sorted(dias):
            marker = " <<<" if d.weekday() == 4 else ""
            print(f"  {d.isoformat()} ({DIA_NAMES[d.weekday()]}) - {t}{marker}")
