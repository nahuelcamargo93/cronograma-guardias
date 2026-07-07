import sqlite3
from datetime import date, timedelta

conn = sqlite3.connect('cronograma_inteligente.db')

# Último cronograma del servicio 1
crono_id = 601

# Verificar qué días tiene Toledo asignada
rows = conn.execute("""
    SELECT g.fecha, g.turno
    FROM guardias g
    WHERE g.cronograma_id = ? AND g.nombre = 'Toledo, Andrea'
    ORDER BY g.fecha
""", (crono_id,)).fetchall()

print(f"=== TOLEDO, ANDREA - Cronograma {crono_id} ===")
for fecha, turno in rows:
    d = date.fromisoformat(fecha)
    dia_semana = ['Lun','Mar','Mie','Jue','Vie','Sab','Dom'][d.weekday()]
    print(f"  {fecha} ({dia_semana}): {turno}")

# Verificar FLR asignados a Toledo
flrs = conn.execute("""
    SELECT fecha_inicio, fecha_fin
    FROM flr_asignados
    WHERE cronograma_id = ? AND nombre = 'Toledo, Andrea'
""", (crono_id,)).fetchall()
print(f"\nFLR asignados: {flrs}")

# Mostrar días hábiles SIN asignación
print("\n=== DÍAS HÁBILES SIN ASIGNACIÓN ===")
inicio = date(2026, 8, 1)
fin = date(2026, 8, 31)
fechas_asignadas = {r[0] for r in rows}
d = inicio
while d <= fin:
    if d.weekday() < 5 and d.isoformat() not in fechas_asignadas:
        dia_semana = ['Lun','Mar','Mie','Jue','Vie','Sab','Dom'][d.weekday()]
        print(f"  {d.isoformat()} ({dia_semana}) - SIN TURNO")
    d += timedelta(days=1)
