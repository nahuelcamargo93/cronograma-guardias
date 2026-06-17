import sqlite3
import datetime

conn = sqlite3.connect("cronograma_inteligente.db")
crono_id = 438

# Let's mimic the historical query from equidad_finds_mensual.py
# peso_cfg: {"peso": 5000, "tipo": "HISTORICA", "fecha_inicio": "2026-06-22"}
fecha_inicio_niv_str = "2026-06-22"
fecha_inicio_dt = datetime.date.fromisoformat("2026-06-22")
fecha_fin_hist_dt = fecha_inicio_dt - datetime.timedelta(days=1)
fecha_fin_hist_str = fecha_fin_hist_dt.isoformat()

print(f"Buscando historiales desde {fecha_inicio_niv_str} hasta {fecha_fin_hist_str}")

cronos = conn.execute("""
    SELECT DISTINCT c.id, c.fecha_inicio, c.fecha_fin
    FROM cronogramas c
    JOIN guardias g ON c.id = g.cronograma_id
    JOIN personal p ON g.nombre = p.nombre
    WHERE p.servicio_id = 1
      AND c.estado = 'aprobado'
      AND c.fecha_inicio >= ?
      AND c.fecha_fin <= ?
    ORDER BY c.fecha_inicio
""", (fecha_inicio_niv_str, fecha_fin_hist_str)).fetchall()

print(f"Cronogramas aprobados encontrados en rango: {len(cronos)}")
for c in cronos:
    print(f"  Crono {c[0]}: {c[1]} a {c[2]}")

if cronos:
    crono_ids = [c[0] for c in cronos]
    placeholders = ",".join("?" for _ in crono_ids)
    
    guardias_hist = conn.execute(f"""
        SELECT g.nombre, g.fecha, g.cronograma_id
        FROM guardias g
        JOIN personal p ON g.nombre = p.nombre
        WHERE g.cronograma_id IN ({placeholders})
          AND g.es_finde = 1
          AND p.servicio_id = 1
    """, crono_ids).fetchall()

    guardias_por_finde = {}
    for nom, fecha_str, c_id in guardias_hist:
        f_dt = datetime.date.fromisoformat(fecha_str)
        wd = f_dt.weekday()
        if wd in (5, 6):
            lunes_dt = f_dt - datetime.timedelta(days=wd)
            lunes_str = lunes_dt.isoformat()
            guardias_por_finde.setdefault(nom, {}).setdefault((c_id, lunes_str), set()).add(wd)

    completos_historicos = {}
    medios_historicos = {}
    
    # We want to see how many weekend shifts are assigned to Jefe/Coordinadores and others
    personal = conn.execute("SELECT nombre, rol FROM personal WHERE servicio_id = 1 AND activo = 1").fetchall()

    for nom, findes_dict in guardias_por_finde.items():
        c_count = 0
        m_count = 0
        for (c_id, lunes_str), wds in findes_dict.items():
            if len(wds) >= 2:
                c_count += 1
            elif len(wds) == 1:
                m_count += 1
        completos_historicos[nom] = c_count
        medios_historicos[nom] = m_count

    print("\n=== HISTÓRICO DE FINES DE SEMANA (RECOLECTADO) ===")
    for name, rol in sorted(personal, key=lambda x: (x[1], x[0])):
        ch = completos_historicos.get(name, 0)
        mh = medios_historicos.get(name, 0)
        print(f"{name} ({rol}): Completos: {ch}, Medios: {mh}")
else:
    print("No hay cronogramas históricos aprobados en el rango especificado.")
    
# Let's query ALL approved cronogramas in the database to see their date ranges
print("\n=== TODOS LOS CRONOGRAMAS APROBADOS ===")
all_cronos = conn.execute("SELECT id, fecha_inicio, fecha_fin, notas, estado FROM cronogramas WHERE estado = 'aprobado' ORDER BY fecha_inicio").fetchall()
for c in all_cronos:
    # count guardias for this crono to see if it has service 1 guardias
    cnt = conn.execute("SELECT COUNT(*) FROM guardias g JOIN personal p ON g.nombre = p.nombre WHERE g.cronograma_id = ? AND p.servicio_id = 1", (c[0],)).fetchone()[0]
    print(f"Crono {c[0]}: {c[1]} a {c[2]}, Estado: {c[4]}, Guardias Serv 1: {cnt}, Notas: {c[3]}")

conn.close()
