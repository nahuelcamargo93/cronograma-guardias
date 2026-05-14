import sqlite3
from datetime import date, timedelta

conn = sqlite3.connect('cronograma_inteligente.db')

sem_inicio = date(2026, 6, 1)
sem_fin    = date(2026, 6, 7)

rows = conn.execute('''
    SELECT nombre, tipo, fecha_inicio, fecha_fin
    FROM licencias
    WHERE fecha_inicio <= ? AND fecha_fin >= ?
    ORDER BY nombre
''', (sem_fin.isoformat(), sem_inicio.isoformat())).fetchall()

print("Licencias activas en semana 01/06 - 07/06:")
print("-" * 60)
for nombre, tipo, fi, ff in rows:
    fi_dt = date.fromisoformat(fi)
    ff_dt = date.fromisoformat(ff)
    dias = sum(1 for d in range(7) if fi_dt <= sem_inicio + timedelta(days=d) <= ff_dt)
    semana_completa = "COMPLETA" if dias == 7 else f"{dias} dia/s"
    print(f"  {nombre:<20} {tipo}  {fi} -> {ff}  ({semana_completa})")

print(f"\nTotal personas afectadas: {len(rows)}")
conn.close()
