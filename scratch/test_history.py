import sqlite3
from datetime import date, timedelta

conn = sqlite3.connect("cronograma_inteligente.db")
servicio_id = 1
fecha_inicio_dt = date.fromisoformat("2026-06-22")
fecha_inicio_niv_str = "2026-01-01"

fecha_fin_hist_dt = fecha_inicio_dt - timedelta(days=1)
fecha_fin_hist_str = fecha_fin_hist_dt.isoformat()

cronos = conn.execute("""
    SELECT DISTINCT c.id, c.fecha_inicio, c.fecha_fin
    FROM cronogramas c
    JOIN guardias g ON c.id = g.cronograma_id
    JOIN personal p ON g.nombre = p.nombre
    WHERE p.servicio_id = ?
      AND c.estado = 'aprobado'
      AND c.fecha_inicio >= ?
      AND c.fecha_fin <= ?
    ORDER BY c.fecha_inicio
""", (servicio_id, fecha_inicio_niv_str, fecha_fin_hist_str)).fetchall()

print(f"Historical cronogramas found: {len(cronos)}")
for c in cronos:
    print(f"  ID: {c[0]}, Range: {c[1]} to {c[2]}")

if cronos:
    crono_ids = [c[0] for c in cronos]
    placeholders = ",".join("?" for _ in crono_ids)
    guardias_hist = conn.execute(f"""
        SELECT g.nombre, g.fecha, g.cronograma_id
        FROM guardias g
        JOIN personal p ON g.nombre = p.nombre
        WHERE g.cronograma_id IN ({placeholders})
          AND g.es_finde = 1
          AND p.servicio_id = ?
    """, crono_ids + [servicio_id]).fetchall()
    
    guardias_por_finde = {}
    for nom, fecha_str, c_id in guardias_hist:
        f_dt = date.fromisoformat(fecha_str)
        wd = f_dt.weekday()
        if wd in (5, 6):
            lunes_dt = f_dt - timedelta(days=wd)
            lunes_str = lunes_dt.isoformat()
            guardias_por_finde.setdefault(nom, {}).setdefault((c_id, lunes_str), set()).add(wd)
            
    print("\n=== HISTORICAL SHIFTS PER EMPLOYEE ===")
    for nom, findes_dict in sorted(guardias_por_finde.items()):
        c_count = 0
        m_count = 0
        for (c_id, lunes_str), wds in findes_dict.items():
            if len(wds) >= 2:
                c_count += 1
            elif len(wds) == 1:
                m_count += 1
        print(f"{nom}: completos={c_count}, medios={m_count}")

conn.close()
