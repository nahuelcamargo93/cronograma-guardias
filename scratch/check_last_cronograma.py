import sqlite3
import json
import sys
import os
from datetime import datetime, date, timedelta

# Add root folder to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

conn = sqlite3.connect("cronograma_inteligente.db")
cur = conn.cursor()

# Get the last cronograma for service 3
cur.execute("SELECT id, fecha_inicio, fecha_fin, creado_en, notas, estado FROM cronogramas ORDER BY id DESC")
cronogramas = cur.fetchall()
print("--- ALL CRONOGRAMAS ---")
for c in cronogramas[:10]:
    print(c)

# Let's check the last one
if cronogramas:
    last_c_id = cronogramas[0][0]
    last_c_inicio = cronogramas[0][1]
    last_c_fin = cronogramas[0][2]
    print(f"\nAnalyzing cronograma ID: {last_c_id} ({last_c_inicio} -> {last_c_fin})")

    # Get personal rules and adjustments for this cronograma
    cur.execute("SELECT DISTINCT nombre FROM guardias WHERE cronograma_id = ?", (last_c_id,))
    empleados = [r[0] for r in cur.fetchall()]
    print(f"Employees in this cronograma: {len(empleados)}")

    # Regla de servicio:
    cur.execute("SELECT parametros_json FROM servicios_reglas WHERE servicio_id = 3 AND codigo_regla = 'EXACTO_FINDE_Y_DIA'")
    row_srv = cur.fetchone()
    srv_params = json.loads(row_srv[0]) if row_srv else {}
    print(f"Service rule parameters: {srv_params}")

    # For each employee:
    for emp_name in sorted(empleados):
        # Load any rule adjustments for this employee in the range
        cur.execute("""
            SELECT accion, parametros_json, fecha_inicio, fecha_fin FROM personal_reglas_ajustes 
            WHERE personal_nombre = ? AND codigo_regla = 'EXACTO_FINDE_Y_DIA'
              AND fecha_inicio <= ? AND fecha_fin >= ? AND activo = 1
        """, (emp_name, last_c_fin, last_c_inicio))
        ajustes = cur.fetchall()
        
        params = srv_params
        status_msg = ""
        if ajustes:
            # Sort by ID descending or choose the one that overlaps best.
            # For simplicity, if there's any active adjustment:
            accion, adj_json, fi, ff = ajustes[0]
            if accion == 'SUSPENDER':
                print(f"{emp_name}: Rule EXACTO_FINDE_Y_DIA is SUSPENDED ({fi} to {ff}).")
                continue
            elif accion == 'SOBRESCRIBIR' and adj_json:
                params = json.loads(adj_json)
                status_msg = f" (OVERRIDDEN: {fi} to {ff})"
        
        # Let's calculate availability
        # Licencias
        cur.execute("""
            SELECT fecha_inicio, fecha_fin FROM licencias 
            WHERE nombre = ? AND fecha_inicio <= ? AND fecha_fin >= ?
        """, (emp_name, last_c_fin, last_c_inicio))
        lics = cur.fetchall()
        dias_licencia = set()
        fecha_inicio_dt = date.fromisoformat(last_c_inicio)
        fecha_fin_dt = date.fromisoformat(last_c_fin)
        dias_del_bloque = (fecha_fin_dt - fecha_inicio_dt).days + 1
        
        for l_ini, l_fin in lics:
            li = max(date.fromisoformat(l_ini), fecha_inicio_dt)
            lf = min(date.fromisoformat(l_fin), fecha_fin_dt)
            d = li
            while d <= lf:
                dias_licencia.add((d - fecha_inicio_dt).days)
                d += timedelta(days=1)
        
        # Francos forzados
        dias_franco_forzado = set()
        cur.execute("""
            SELECT fecha_inicio, fecha_fin FROM personal_reglas_ajustes
            WHERE personal_nombre = ? AND codigo_regla = 'FRANCO_FORZADO'
              AND fecha_inicio <= ? AND fecha_fin >= ? AND activo = 1
        """, (emp_name, last_c_fin, last_c_inicio))
        ffs = cur.fetchall()
        for f_ini, f_fin in ffs:
            fi = max(date.fromisoformat(f_ini), fecha_inicio_dt)
            ff = min(date.fromisoformat(f_fin), fecha_fin_dt)
            d = fi
            while d <= ff:
                dias_franco_forzado.add((d - fecha_inicio_dt).days)
                d += timedelta(days=1)
                
        # Offset
        offset_dia = fecha_inicio_dt.weekday()
        
        # Feriados: load from database / data.py
        from data import FERIADOS
        feriados_indices = []
        for f_str in FERIADOS:
            f_dt = date.fromisoformat(f_str)
            if fecha_inicio_dt <= f_dt <= fecha_fin_dt:
                feriados_indices.append((f_dt - fecha_inicio_dt).days)
                
        def is_finde(d):
            return ((d + offset_dia) % 7) >= 5 or d in feriados_indices

        # Calculate k (available weekends)
        findes = {}
        for d in range(dias_del_bloque):
            fecha_d = fecha_inicio_dt + timedelta(days=d)
            if is_finde(d):
                lunes = (fecha_d - timedelta(days=fecha_d.weekday())).isoformat()
                findes.setdefault(lunes, []).append(d)
        
        k = sum(1 for lunes, dias in findes.items() if any(d not in dias_licencia for d in dias))
        
        # Calculate k_dia
        mapa_dias = {"lunes": 0, "martes": 1, "miercoles": 2, "jueves": 3, "viernes": 4, "sabado": 5, "domingo": 6}
        dia_conf = params.get('dia_semana', 4)
        if isinstance(dia_conf, str):
            dia_str = dia_conf.lower().replace('é', 'e').replace('á', 'a').replace('í', 'i').replace('ó', 'o').replace('ú', 'u')
            dia_semana_target = mapa_dias.get(dia_str, 4)
        else:
            dia_semana_target = int(dia_conf)
            
        k_dia = 0
        for d in range(dias_del_bloque):
            fecha_d = fecha_inicio_dt + timedelta(days=d)
            if fecha_d.weekday() == dia_semana_target:
                if d in dias_licencia or d in dias_franco_forzado:
                    continue
                k_dia += 1
                
        # Targets
        mapping_findes = params.get('findes_por_disponibilidad')
        if mapping_findes:
            target_findes = mapping_findes.get(str(k), mapping_findes.get(k, 0))
        else:
            target_findes = 0
            
        mapping_dias = params.get('dias_por_disponibilidad')
        if mapping_dias:
            target_dias = mapping_dias.get(str(k_dia), mapping_dias.get(k_dia, 0))
        else:
            target_dias = 0
            
        # Count actually worked weekends and specified days in guardias
        cur.execute("SELECT fecha, turno, horas FROM guardias WHERE cronograma_id = ? AND nombre = ?", (last_c_id, emp_name))
        guardias_trabajadas = cur.fetchall()
        
        findes_trabajados = set()
        dias_trabajados = 0
        
        for g_fecha_str, g_turno, g_horas in guardias_trabajadas:
            g_fecha = date.fromisoformat(g_fecha_str)
            d_idx = (g_fecha - fecha_inicio_dt).days
            if is_finde(d_idx):
                lunes = (g_fecha - timedelta(days=g_fecha.weekday())).isoformat()
                findes_trabajados.add(lunes)
            if g_fecha.weekday() == dia_semana_target:
                dias_trabajados += 1
                
        status = "OK"
        details = []
        if len(findes_trabajados) != target_findes:
            status = "FAIL"
            details.append(f"findes mismatch (worked {len(findes_trabajados)} vs target {target_findes})")
        if dias_trabajados != target_dias:
            status = "FAIL"
            details.append(f"dias mismatch (worked {dias_trabajados} vs target {target_dias})")
            
        print(f"{emp_name}{status_msg}: {status} {', '.join(details) if details else ''}")
        print(f"  k_findes: {k}, target_findes: {target_findes}, worked: {len(findes_trabajados)}")
        print(f"  k_dias: {k_dia}, target_dias: {target_dias}, worked: {dias_trabajados}")

conn.close()
