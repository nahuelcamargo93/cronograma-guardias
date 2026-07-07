import sqlite3
from datetime import date, timedelta

conn = sqlite3.connect('cronograma_inteligente.db')

for nombre, crono_id in [('Toledo, Andrea', 604), ('Garcia, Luciano', 604)]:
    rows = conn.execute("SELECT fecha, turno FROM guardias WHERE cronograma_id = ? AND nombre = ? ORDER BY fecha", (crono_id, nombre)).fetchall()
    fechas = {r[0] for r in rows}
    
    print(f"\n=== {nombre} - Crono {crono_id} ===")
    faltantes = []
    d = date(2026, 8, 1)
    for i in range(31):
        d2 = d + timedelta(days=i)
        if d2.weekday() < 5 and d2.isoformat() not in fechas:
            dia = ['Lun','Mar','Mie','Jue','Vie'][d2.weekday()]
            faltantes.append(f"{d2.isoformat()} ({dia})")
    
    flrs = conn.execute("SELECT fecha_inicio, fecha_fin FROM flr_asignados WHERE cronograma_id = ? AND nombre = ?", (crono_id, nombre)).fetchall()
    print(f"FLR: {flrs}")
    print(f"Dias habiles faltantes: {faltantes if faltantes else 'NINGUNO'}")
