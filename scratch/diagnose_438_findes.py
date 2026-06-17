import sqlite3
import datetime

conn = sqlite3.connect("cronograma_inteligente.db")
crono_id = 438

crono = conn.execute("SELECT id, fecha_inicio, fecha_fin, notas, estado FROM cronogramas WHERE id = ?", (crono_id,)).fetchone()
print(f"CRONOGRAMA DETALLES: {crono}")

if crono:
    fecha_inicio, fecha_fin = crono[1], crono[2]
    
    # Let's count weekend days in this range
    f_ini_dt = datetime.date.fromisoformat(fecha_inicio)
    f_fin_dt = datetime.date.fromisoformat(fecha_fin)
    dias = (f_fin_dt - f_ini_dt).days + 1
    
    print(f"Rango: {fecha_inicio} a {fecha_fin} ({dias} dias)")
    
    # Get all weekend guardias for this crono
    rows = conn.execute(
        "SELECT nombre, fecha, turno FROM guardias WHERE cronograma_id = ?", (crono_id,)
    ).fetchall()
    
    # We want to see how many weekend shifts are assigned to Jefe/Coordinadores and others
    personal = conn.execute("SELECT nombre, rol FROM personal WHERE servicio_id = 1 AND activo = 1").fetchall()
    personal_rol = {p[0]: p[1] for p in personal}
    
    weekend_shifts = {}
    total_shifts = {}
    
    for name, f_str, turno in rows:
        total_shifts[name] = total_shifts.get(name, 0) + 1
        dt = datetime.datetime.strptime(f_str, "%Y-%m-%d")
        if dt.weekday() in (5, 6):
            weekend_shifts.setdefault(name, []).append((f_str, turno))
            
    print("\n=== ASIGNACIONES EN CRONOGRAMA ===")
    for name, rol in sorted(personal, key=lambda x: (x[1], x[0])):
        w_shifts = weekend_shifts.get(name, [])
        t_shifts = total_shifts.get(name, 0)
        print(f"{name} ({rol}): Total: {t_shifts}, Findes: {len(w_shifts)}")
        for f_str, turno in w_shifts:
            print(f"   - Finde: {f_str} ({turno})")

    # Let's check demand_config for weekends in UTI/UCO (the puestos for Jefe/Coordinador)
    print("\n=== DEMANDA CONFIG FINES DE SEMANA PARA PUESTOS DE SERVICIO 1 ===")
    demands = conn.execute("""
        SELECT p.nombre, dc.tipo_dia, dc.hora_inicio, dc.hora_fin, dc.cantidad_min, dc.cantidad_max
        FROM demanda_config dc
        JOIN puestos p ON dc.puesto_id = p.id
        WHERE p.servicio_id = 1 AND dc.activo = 1 AND dc.tipo_dia = 'Finde_Feriado'
    """).fetchall()
    for row in demands:
        print(f"Puesto: {row[0]}, Tipo: {row[1]}, Inicio: {row[2]}, Fin: {row[3]}, Min: {row[4]}, Max: {row[5]}")

    # Let's check turnos_config for weekends in UTI/UCO
    print("\n=== TURNOS CONFIG FINES DE SEMANA PARA SERVICIO 1 ===")
    turnos = conn.execute("""
        SELECT tc.nombre, tc.hora_inicio, tc.horas, tc.dias_semana, p.nombre
        FROM turnos_config tc
        LEFT JOIN puestos p ON tc.puesto_id = p.id
        WHERE tc.servicio_id = 1 AND tc.activo = 1
    """).fetchall()
    for row in turnos:
        print(f"Turno: {row[0]}, Inicio: {row[1]}, Horas: {row[2]}, Dias: {row[3]}, Puesto: {row[4]}")

conn.close()
