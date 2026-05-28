import sys; sys.path.insert(0,'.')
from database.connection import get_connection
from collections import defaultdict
conn = get_connection()
cur = conn.cursor()

# Check feriados distribution for cronograma 200
# First, find what feriados existed in that period
cur.execute("""
    SELECT fecha_inicio, fecha_fin FROM cronogramas WHERE id = 200
""")
row = conn.execute("SELECT fecha_inicio, fecha_fin FROM cronogramas WHERE id = 200").fetchone()
if row:
    fi, ff = row
    print(f"Cronograma 200: {fi} a {ff}")

# Get all guardias for cronograma 200 with dates
rows = conn.execute("""
    SELECT g.nombre, g.fecha, g.turno
    FROM guardias g
    JOIN personal p ON g.nombre = p.nombre
    WHERE g.cronograma_id = 200 AND p.servicio_id = 4
    ORDER BY g.nombre, g.fecha
""").fetchall()

from datetime import date
FERIADOS = ['2026-06-20']  # Adjust based on actual data

# Count weekends and feriados per person
weekend_days = defaultdict(int)
feriado_days = defaultdict(int)
weekend_count_map = defaultdict(set)  # (year, week) -> set of weekday

for nombre, fecha, turno in rows:
    dt = date.fromisoformat(fecha)
    wd = dt.weekday()  # 0=Mon, 5=Sat, 6=Sun
    if wd >= 5:
        weekend_days[nombre] += 1
        iso = dt.isocalendar()
        weekend_count_map[nombre].add((iso[0], iso[1]))
    if fecha in FERIADOS:
        feriado_days[nombre] += 1

# Count full weekends (worked both Sat and Sun in same week)
# For simplicity, count distinct (year, week) pairs
print('\nWEEKEND STATS (by distinct week):')
for nombre in sorted(set(r[0] for r in rows)):
    w = len(weekend_count_map[nombre])
    wd = weekend_days[nombre]
    f = feriado_days[nombre]
    print(f"  {nombre}: {w} fines de semana, {wd} días de finde, {f} feriados")

conn.close()
