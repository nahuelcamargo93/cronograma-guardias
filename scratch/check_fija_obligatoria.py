import sqlite3
from datetime import date, timedelta

conn = sqlite3.connect('cronograma_inteligente.db')
crono_id = 603

print(f"=== TOLEDO, ANDREA - Cronograma {crono_id} ===")
rows = conn.execute("SELECT fecha, turno FROM guardias WHERE cronograma_id = ? AND nombre = 'Toledo, Andrea' ORDER BY fecha", (crono_id,)).fetchall()
for fecha, turno in rows:
    d = date.fromisoformat(fecha)
    dia = ['Lun','Mar','Mie','Jue','Vie','Sab','Dom'][d.weekday()]
    print(f"  {fecha} ({dia}): {turno}")

flrs = conn.execute("SELECT fecha_inicio, fecha_fin FROM flr_asignados WHERE cronograma_id = ? AND nombre = 'Toledo, Andrea'", (crono_id,)).fetchall()
print(f"\nFLR: {flrs}")

print("\n=== DÍAS HÁBILES SIN ASIGNACIÓN ===")
fechas = {r[0] for r in rows}
d = date(2026, 8, 1)
sin = []
while d <= date(2026, 8, 31):
    if d.weekday() < 5 and d.isoformat() not in fechas:
        dia = ['Lun','Mar','Mie','Jue','Vie','Sab','Dom'][d.weekday()]
        sin.append(f"  {d.isoformat()} ({dia})")
    d += timedelta(days=1)
if sin:
    print('\n'.join(sin))
else:
    print("  NINGUNO - Todos los días hábiles cubiertos ✓")

# Verificar Garcia también
print(f"\n=== GARCIA, LUCIANO - Cronograma {crono_id} ===")
rows2 = conn.execute("SELECT fecha, turno FROM guardias WHERE cronograma_id = ? AND nombre = 'Garcia, Luciano' ORDER BY fecha", (crono_id,)).fetchall()
for fecha, turno in rows2:
    d = date.fromisoformat(fecha)
    dia = ['Lun','Mar','Mie','Jue','Vie','Sab','Dom'][d.weekday()]
    print(f"  {fecha} ({dia}): {turno}")

flrs2 = conn.execute("SELECT fecha_inicio, fecha_fin FROM flr_asignados WHERE cronograma_id = ? AND nombre = 'Garcia, Luciano'", (crono_id,)).fetchall()
print(f"\nFLR: {flrs2}")

print("\n=== DÍAS HÁBILES SIN ASIGNACIÓN ===")
fechas2 = {r[0] for r in rows2}
d = date(2026, 8, 1)
sin2 = []
while d <= date(2026, 8, 31):
    if d.weekday() < 5 and d.isoformat() not in fechas2:
        dia = ['Lun','Mar','Mie','Jue','Vie','Sab','Dom'][d.weekday()]
        sin2.append(f"  {d.isoformat()} ({dia})")
    d += timedelta(days=1)
if sin2:
    print('\n'.join(sin2))
else:
    print("  NINGUNO - Todos los días hábiles cubiertos ✓")
