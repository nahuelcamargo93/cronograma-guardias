import pandas as pd
from datetime import date, timedelta
from database import queries as database
from reportes.base import BaseReport

def exportar_excel_data_prep(df_resultados, config_turnos):
    # --- PIVOTEAR EL CRONOGRAMA ---
    df_excel = df_resultados.copy()
    
    # Desdoblar turnos combinados (MT y TNN) solo para la vista
    filas_extra = []
    indices_a_borrar = []
    for idx, row in df_excel.iterrows():
        if row['Turno'] == 'MT':
            row_m = row.copy(); row_m['Turno'] = "M"; filas_extra.append(row_m)
            row_t = row.copy(); row_t['Turno'] = "T"; filas_extra.append(row_t)
            indices_a_borrar.append(idx)
        elif row['Turno'] == 'TNN':
            row_tn = row.copy(); row_tn['Turno'] = "TN"; filas_extra.append(row_tn)
            # La parte N de un TNN ocurre al día siguiente
            row_n = row.copy(); row_n['Turno'] = "N"
            try:
                curr_date = date.fromisoformat(row_n['Fecha'])
                row_n['Fecha'] = (curr_date + timedelta(days=1)).isoformat()
                filas_extra.append(row_n)
            except:
                filas_extra.append(row_n) 
            indices_a_borrar.append(idx)
            
    df_excel = df_excel.drop(indices_a_borrar)
    if filas_extra:
        df_excel = pd.concat([df_excel, pd.DataFrame(filas_extra)], ignore_index=True)
        
    fechas_originales = sorted(df_resultados['Fecha'].unique())
    fechas_unicas = sorted(df_excel['Fecha'].unique())
    
    if fechas_originales:
        fecha_limite_exclusiva = (date.fromisoformat(fechas_originales[-1]) + timedelta(days=1)).isoformat()
        fechas_unicas = [f for f in fechas_unicas if f < fecha_limite_exclusiva]
    
    turnos_ordenados = ["N", "M", "T", "TN"]
    filas_excel = []

    for turno_label in turnos_ordenados:
        df_turno = df_excel[df_excel['Turno'] == turno_label]
        
        # Cálculo de max_personas_turno
        max_p = 0
        for f in fechas_unicas:
            c = len(df_turno[df_turno['Fecha'] == f])
            if c > max_p: max_p = c
        max_personas_turno = max(1, max_p)

        for i in range(max_personas_turno):
            fila = {"Turno": turno_label}
            for fecha in fechas_unicas:
                pers_dia = df_turno[df_turno['Fecha'] == fecha].sort_values(by='Kinesiologo')['Kinesiologo'].tolist()
                fila[fecha] = pers_dia[i] if i < len(pers_dia) else ""
            filas_excel.append(fila)

    # Filas de Licencias
    filas_excel.append({"Turno": "  "}) 
    fila_lpp = {"Turno": "LPP"}
    fila_lar = {"Turno": "LAR"}
    fila_lm = {"Turno": "LM"}
    fila_cm = {"Turno": "CM"}

    for fecha in fechas_unicas:
        fecha_dt = date.fromisoformat(fecha)
        nombres_lpp = [n for n, r in database.LPP.items() if any(date.fromisoformat(i) <= fecha_dt <= date.fromisoformat(f) for i, f in r)]
        fila_lpp[fecha] = "\n".join(nombres_lpp)
        nombres_lar = [n for n, r in database.LAR.items() if any(date.fromisoformat(i) <= fecha_dt <= date.fromisoformat(f) for i, f in r)]
        fila_lar[fecha] = "\n".join(nombres_lar)
        nombres_lm = [n for n, r in getattr(database, 'LM', {}).items() if any(date.fromisoformat(i) <= fecha_dt <= date.fromisoformat(f) for i, f in r)]
        fila_lm[fecha] = "\n".join(nombres_lm)
        nombres_cm = [n for n, r in getattr(database, 'CM', {}).items() if any(date.fromisoformat(i) <= fecha_dt <= date.fromisoformat(f) for i, f in r)]
        fila_cm[fecha] = "\n".join(nombres_cm)

    filas_excel.append(fila_lpp)
    filas_excel.append(fila_lar)
    filas_excel.append(fila_lm)
    filas_excel.append(fila_cm)

    df_pivot = pd.DataFrame(filas_excel).set_index("Turno")
    return df_pivot, fechas_unicas

def exportar_excel_vista_personal(df_resultados, df_personal, flrs_asignados=None):
    fechas = sorted(df_resultados['Fecha'].unique())
    nombres = sorted(df_personal['Nombre'].tolist())
    
    mapa_flrs = {}
    if flrs_asignados:
        for flr in flrs_asignados:
            n = flr['nombre']
            fi = date.fromisoformat(flr['fecha_inicio'])
            ff = date.fromisoformat(flr['fecha_fin'])
            mapa_flrs.setdefault(n, []).append((fi, ff))

    def asignar_horas_enf(t):
        return 12 if t in ["MT", "TNN"] else 6 if t in ["M", "T", "TN", "N"] else 0

    filas = []
    for nombre in nombres:
        fila = {"Enfermero": nombre}
        total_horas_efectivas = 0
        total_f = 0
        dias_licencia = 0
        for fecha in fechas:
            fecha_dt = date.fromisoformat(fecha)
            asig = df_resultados[(df_resultados['Kinesiologo'] == nombre) & (df_resultados['Fecha'] == fecha)]
            if not asig.empty:
                t = asig.iloc[0]['Turno']
                fila[fecha] = t
                total_horas_efectivas += asignar_horas_enf(t)
            else:
                es_flr = any(fi <= fecha_dt <= ff for fi, ff in mapa_flrs.get(nombre, []))
                es_lar = any(date.fromisoformat(i) <= fecha_dt <= date.fromisoformat(f) for i, f in database.LAR.get(nombre, []))
                es_lpp = any(date.fromisoformat(i) <= fecha_dt <= date.fromisoformat(f) for i, f in database.LPP.get(nombre, []))
                es_lm = any(date.fromisoformat(i) <= fecha_dt <= date.fromisoformat(f) for i, f in getattr(database, 'LM', {}).get(nombre, []))
                es_cm = any(date.fromisoformat(i) <= fecha_dt <= date.fromisoformat(f) for i, f in getattr(database, 'CM', {}).get(nombre, []))

                if es_flr: fila[fecha] = "FLR"
                elif es_lar: fila[fecha] = "LAR"; dias_licencia += 1
                elif es_lpp: fila[fecha] = "LPP"; dias_licencia += 1
                elif es_lm: fila[fecha] = "LM"; dias_licencia += 1
                elif es_cm: fila[fecha] = "CM"; dias_licencia += 1
                else: fila[fecha] = "F"; total_f += 1
        
        dias_periodo = len(fechas)
        horas_licencia = round((144.0 / dias_periodo) * dias_licencia, 1) if dias_periodo > 0 else 0
        
        fila["H. Efectivas"] = total_horas_efectivas
        fila["H. Licencia"] = horas_licencia
        fila["H. Totales"] = total_horas_efectivas + horas_licencia
        fila["F"] = total_f
        filas.append(fila)
        
    return pd.DataFrame(filas).set_index("Enfermero")

def generar_reporte_horas(df_resultados):
    df_reporte_horas = df_resultados.copy()
    def asignar_horas_enf(t):
        return 12 if t in ["MT", "TNN"] else 6
    df_reporte_horas['Horas'] = df_reporte_horas['Turno'].apply(asignar_horas_enf)
    horas_por_persona = df_reporte_horas.groupby('Kinesiologo')['Horas'].sum().reset_index()
    reporte_final = horas_por_persona.rename(columns={'Kinesiologo': 'Enfermero', 'Horas': 'Horas Mensuales'})
    return reporte_final.sort_values(by='Horas Mensuales', ascending=False).reset_index(drop=True)

def asignar_horas_enf(t):
    return 12 if t in ["MT", "TNN"] else 6 if t in ["M", "T", "TN", "N"] else 0

def calcular_metricas_periodo(nombre, guardias, fecha_inicio_dt, fecha_fin_dt, feriados_set):
    """
    Calcula las métricas de un enfermero en un período específico.
    guardias es una lista de dicts con 'fecha', 'turno', 'horas'.
    """
    # 1. Horas Efectivas
    horas_efectivas = sum(g['horas'] for g in guardias)
    
    # 2. Fines de Semana
    weekends_worked = {}
    for g in guardias:
        f_str = g['fecha']
        dt = date.fromisoformat(f_str)
        if fecha_inicio_dt <= dt <= fecha_fin_dt:
            wd = dt.weekday()
            if wd in (5, 6):
                iso_yr, iso_wk, _ = dt.isocalendar()
                weekends_worked.setdefault((iso_yr, iso_wk), set()).add(wd)
                
    fs_trabajado = 0
    medio_fs_trabajado = 0
    for week_key, wds in weekends_worked.items():
        if 5 in wds and 6 in wds:
            fs_trabajado += 1
        else:
            medio_fs_trabajado += 1
            
    # 3. Feriados
    feriados_trabajados = sum(1 for g in guardias if g['fecha'] in feriados_set)
    
    return horas_efectivas, fs_trabajado, medio_fs_trabajado, feriados_trabajados

def calcular_dias_licencia_periodo(nombre, fecha_inicio_dt, fecha_fin_dt):
    # Asegurar que las licencias en memoria estén cargadas
    if not database.LAR and not database.LPP:
        database.init_licencias()

    dias_licencia = 0
    dias_periodo = (fecha_fin_dt - fecha_inicio_dt).days + 1
    for i in range(dias_periodo):
        curr_dt = fecha_inicio_dt + timedelta(days=i)
        
        es_lar = any(date.fromisoformat(start) <= curr_dt <= date.fromisoformat(end) for start, end in database.LAR.get(nombre, []))
        es_lpp = any(date.fromisoformat(start) <= curr_dt <= date.fromisoformat(end) for start, end in database.LPP.get(nombre, []))
        es_lm = any(date.fromisoformat(start) <= curr_dt <= date.fromisoformat(end) for start, end in getattr(database, 'LM', {}).get(nombre, []))
        es_cm = any(date.fromisoformat(start) <= curr_dt <= date.fromisoformat(end) for start, end in getattr(database, 'CM', {}).get(nombre, []))
        
        if es_lar or es_lpp or es_lm or es_cm:
            dias_licencia += 1
    return dias_licencia

def calcular_findes_habiles_periodo(nombre, fecha_inicio_dt, fecha_fin_dt):
    # Asegurar que las licencias en memoria estén cargadas
    if not database.LAR and not database.LPP:
        database.init_licencias()

    dias_periodo = (fecha_fin_dt - fecha_inicio_dt).days + 1
    semanas = {}
    for i in range(dias_periodo):
        curr_dt = fecha_inicio_dt + timedelta(days=i)
        lunes = curr_dt - timedelta(days=curr_dt.weekday())
        semanas.setdefault(lunes.isoformat(), []).append(curr_dt)
        
    findes_habiles = 0
    for sem_key, dias in semanas.items():
        sats = [d for d in dias if d.weekday() == 5]
        suns = [d for d in dias if d.weekday() == 6]
        if sats and suns:
            sat = sats[0]
            sun = suns[0]
            
            sat_bloqueado = any(date.fromisoformat(start) <= sat <= date.fromisoformat(end) for start, end in database.LAR.get(nombre, [])) or \
                            any(date.fromisoformat(start) <= sat <= date.fromisoformat(end) for start, end in database.LPP.get(nombre, [])) or \
                            any(date.fromisoformat(start) <= sat <= date.fromisoformat(end) for start, end in getattr(database, 'LM', {}).get(nombre, [])) or \
                            any(date.fromisoformat(start) <= sat <= date.fromisoformat(end) for start, end in getattr(database, 'CM', {}).get(nombre, []))
                            
            sun_bloqueado = any(date.fromisoformat(start) <= sun <= date.fromisoformat(end) for start, end in database.LAR.get(nombre, [])) or \
                            any(date.fromisoformat(start) <= sun <= date.fromisoformat(end) for start, end in database.LPP.get(nombre, [])) or \
                            any(date.fromisoformat(start) <= sun <= date.fromisoformat(end) for start, end in getattr(database, 'LM', {}).get(nombre, [])) or \
                            any(date.fromisoformat(start) <= sun <= date.fromisoformat(end) for start, end in getattr(database, 'CM', {}).get(nombre, []))
                            
            if not sat_bloqueado and not sun_bloqueado:
                findes_habiles += 1
                
    return findes_habiles

def calcular_reportes_enfermeria(df_resultados, df_personal, df_persona, dias_del_bloque, feriados_indices, fecha_inicio):
    from database.connection import get_connection
    from data import FERIADOS as data_feriados
    
    fecha_inicio_dt = date.fromisoformat(fecha_inicio)
    fecha_fin_dt = fecha_inicio_dt + timedelta(days=dias_del_bloque - 1)
    
    # Resolver feriados de este mes
    feriados_set = set()
    if feriados_indices:
        for f in feriados_indices:
            if isinstance(f, int):
                f_str = (fecha_inicio_dt + timedelta(days=f)).isoformat()
                feriados_set.add(f_str)
            else:
                feriados_set.add(str(f))
                
    # Feriados completos para histórico
    feriados_set_completo = set(data_feriados).union(feriados_set)
    
    nombres = sorted(df_personal['Nombre'].tolist())
    
    # --- 1. REPORTE MES ACTUAL ---
    filas_mes = []
    for nombre in nombres:
        # Guardias en el mes actual
        df_emp = df_resultados[df_resultados['Kinesiologo'] == nombre]
        guardias_mes = []
        for _, row in df_emp.iterrows():
            guardias_mes.append({
                'fecha': row['Fecha'],
                'turno': row['Turno'],
                'horas': asignar_horas_enf(row['Turno'])
            })
            
        horas_efectivas, fs, medio_fs, feriados_t = calcular_metricas_periodo(
            nombre, guardias_mes, fecha_inicio_dt, fecha_fin_dt, feriados_set
        )
        fs_habiles = calcular_findes_habiles_periodo(nombre, fecha_inicio_dt, fecha_fin_dt)
        
        # Horas totales con licencias
        horas_totales = df_persona.at[nombre, "H. Totales"] if nombre in df_persona.index else horas_efectivas
        
        filas_mes.append({
            'Nombre': nombre,
            'Horas Totales': int(horas_totales + 0.5) if isinstance(horas_totales, (int, float)) else horas_totales,
            'FS habiles': fs_habiles,
            'FS trabajado': fs,
            '1/2 FS trabajado': medio_fs,
            'Feriados': feriados_t
        })
    df_mes = pd.DataFrame(filas_mes)
    
    # --- 2. REPORTE HISTÓRICO ---
    # Inicializar históricos con el mes actual
    hist_horas_totales = {r['Nombre']: r['Horas Totales'] for r in filas_mes}
    hist_fs_habiles = {r['Nombre']: r['FS habiles'] for r in filas_mes}
    hist_fs_trabajado = {r['Nombre']: r['FS trabajado'] for r in filas_mes}
    hist_medio_fs_trabajado = {r['Nombre']: r['1/2 FS trabajado'] for r in filas_mes}
    hist_feriados = {r['Nombre']: r['Feriados'] for r in filas_mes}
    
    # Traer cronogramas aprobados previos
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, fecha_inicio, fecha_fin
            FROM cronogramas
            WHERE estado = 'aprobado' AND fecha_inicio < ?
        """, (fecha_inicio,))
        cronogramas_previos = cursor.fetchall()
        
        for cron_id, fi_str, ff_str in cronogramas_previos:
            fi_dt = date.fromisoformat(fi_str)
            ff_dt = date.fromisoformat(ff_str)
            dias_c = (ff_dt - fi_dt).days + 1
            
            # Guardias de este cronograma para enfermería (servicio_id = 2)
            cursor.execute("""
                SELECT g.nombre, g.fecha, g.turno, g.horas
                FROM guardias g
                JOIN personal p ON g.nombre = p.nombre
                WHERE g.cronograma_id = ? AND p.servicio_id = 2
            """, (cron_id,))
            guardias_cron = cursor.fetchall()
            
            guardias_by_emp = {nombre: [] for nombre in nombres}
            for nombre, fecha, turno, horas in guardias_cron:
                if nombre in guardias_by_emp:
                    guardias_by_emp[nombre].append({
                        'fecha': fecha,
                        'turno': turno,
                        'horas': horas
                    })
                    
            for nombre in nombres:
                horas_ef, fs, medio_fs, feriados_t = calcular_metricas_periodo(
                    nombre, guardias_by_emp[nombre], fi_dt, ff_dt, feriados_set_completo
                )
                fs_h = calcular_findes_habiles_periodo(nombre, fi_dt, ff_dt)
                dias_lic = calcular_dias_licencia_periodo(nombre, fi_dt, ff_dt)
                horas_lic = (144.0 / dias_c) * dias_lic if dias_c > 0 else 0
                
                hist_horas_totales[nombre] += (horas_ef + horas_lic)
                hist_fs_habiles[nombre] += fs_h
                hist_fs_trabajado[nombre] += fs
                hist_medio_fs_trabajado[nombre] += medio_fs
                hist_feriados[nombre] += feriados_t
                
    filas_hist = []
    for nombre in nombres:
        filas_hist.append({
            'Nombre': nombre,
            'Horas Totales': int(hist_horas_totales[nombre] + 0.5) if isinstance(hist_horas_totales[nombre], (int, float)) else hist_horas_totales[nombre],
            'FS habiles': hist_fs_habiles[nombre],
            'FS trabajado': hist_fs_trabajado[nombre],
            '1/2 FS trabajado': hist_medio_fs_trabajado[nombre],
            'Feriados': hist_feriados[nombre]
        })
    df_historico = pd.DataFrame(filas_hist)
    
    return df_mes, df_historico

def exportar_excel(df_pivot, df_persona, fechas_unicas, df_resultados, df_personal, dias_del_bloque, feriados, fecha_inicio, offset_dia, file_name='Cronograma_Enfermeria_UTI.xlsx', df_cat_semanas=None, crono_id=None):
    report = BaseReport(file_name, feriados=feriados, fecha_inicio=fecha_inicio, crono_id=crono_id)
    
    # 1. Cronograma
    ws_c = report.generar_cronograma_sheet(df_pivot, fechas_unicas)
    if crono_id is not None:
        row_c = len(df_pivot) + 3
        ws_c.write(row_c, 0, "ID Cronograma:", report.styles.total_label)
        ws_c.write(row_c, 1, crono_id, report.styles.total_val)
    
    # 2. Vista por Personal
    ext_cols = ["H. Efectivas", "H. Licencia", "H. Totales"]
    tipos_de_semana = ['M', 'T', 'TN', 'N']
    ext_cols += tipos_de_semana
    
    # Agregar conteo de semanas al df_persona calculando la categoría predominante por semana
    for t_label in tipos_de_semana:
        df_persona[t_label] = 0

    if df_cat_semanas is not None and not df_cat_semanas.empty:
        for nombre, row in df_persona.iterrows():
            person_cats = df_cat_semanas[df_cat_semanas['Nombre'] == nombre]
            for _, cat_row in person_cats.iterrows():
                cat = cat_row['Categoria']
                if cat in tipos_de_semana:
                    df_persona.at[nombre, cat] += 1
    else:
        if not df_resultados.empty:
            df_res_week = df_resultados.copy()
            df_res_week['Fecha_dt'] = pd.to_datetime(df_res_week['Fecha'])
            df_res_week['Fecha_Lunes'] = df_res_week['Fecha_dt'].apply(lambda x: (x - pd.Timedelta(days=x.weekday())).strftime("%Y-%m-%d"))
            
            for nombre, row in df_persona.iterrows():
                df_persona_week = df_res_week[df_res_week['Kinesiologo'] == nombre]
                if not df_persona_week.empty:
                    for fecha_lunes, group in df_persona_week.groupby('Fecha_Lunes'):
                        turnos_sem = group['Turno'].tolist()
                        
                        count_M = turnos_sem.count('M')
                        count_T = turnos_sem.count('T')
                        count_TN = turnos_sem.count('TN')
                        count_N = turnos_sem.count('N')
                        count_MT = turnos_sem.count('MT')
                        count_TNN = turnos_sem.count('TNN')
                        
                        score_M = count_M + count_MT
                        score_T = count_T + count_MT
                        score_TN = count_TN + count_TNN
                        score_N = count_N + count_TNN
                        
                        scores = {
                            'M': score_M,
                            'T': score_T,
                            'TN': score_TN,
                            'N': score_N
                        }
                        
                        # Obtener la categoría predominante (mayor score > 0)
                        max_cat = None
                        max_score = 0
                        for cat in ['M', 'T', 'TN', 'N']:
                            if scores[cat] > max_score:
                                max_score = scores[cat]
                                max_cat = cat
                        
                        if max_cat:
                            df_persona.at[nombre, max_cat] += 1

    ws_p, row_end = report.generar_vista_personal_sheet(df_persona, fechas_unicas, extension_columns=ext_cols, label_personal="ENFERMERO")
    
    # --- TOTALES POR FRANJA (Específico de enfermería) ---
    row_end += 1
    filas_extra = []
    df_base = df_resultados.copy()
    for _, r in df_base.iterrows():
        if r['Turno'] == 'MT':
            m = r.copy(); m['Turno'] = 'M'; filas_extra.append(m)
            t = r.copy(); t['Turno'] = 'T'; filas_extra.append(t)
        elif r['Turno'] == 'TNN':
            tn = r.copy(); tn['Turno'] = 'TN'; filas_extra.append(tn)
            n = r.copy(); n['Turno'] = 'N'
            try: n['Fecha'] = (date.fromisoformat(n['Fecha']) + timedelta(days=1)).isoformat()
            except: pass
            filas_extra.append(n)
        else: filas_extra.append(r)
    df_desdoblado = pd.DataFrame(filas_extra)

    for turno_count in ["M", "T", "TN", "N"]:
        ws_p.write(row_end, 0, f"TOTAL {turno_count}", report.styles.total_label)
        for col_idx, fecha in enumerate(fechas_unicas):
            count = len(df_desdoblado[(df_desdoblado['Fecha'] == fecha) & (df_desdoblado['Turno'] == turno_count)])
            is_sep = report._es_fin_de_semana_sep(fecha)
            ws_p.write(row_end, col_idx + 1, count if count > 0 else 0, report.styles.total_val_week if is_sep else report.styles.total_val)
        row_end += 1

    # At the end of Vista por Personal:
    if crono_id is not None:
        row_end += 2
        ws_p.write(row_end, 0, "ID Cronograma:", report.styles.total_label)
        ws_p.write(row_end, 1, crono_id, report.styles.total_val)

    # 3. Reportes de Horas (Mes actual e Histórico)
    df_mes, df_historico = calcular_reportes_enfermeria(
        df_resultados, df_personal, df_persona, dias_del_bloque, feriados, fecha_inicio
    )
    
    # Nombre del mes en español
    MESES = {
        1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
        5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
        9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
    }
    dt_start = date.fromisoformat(fecha_inicio)
    mes_nombre = f"{MESES[dt_start.month]} {dt_start.year}"
    
    ws_m = report.generar_reporte_resumen_sheet(df_mes, sheet_name=f"Reporte {mes_nombre}")
    if crono_id is not None:
        row_m = len(df_mes) + 3
        ws_m.write(row_m, 0, "ID Cronograma:", report.styles.total_label)
        ws_m.write(row_m, 1, crono_id, report.styles.total_val)
        
    ws_h = report.generar_reporte_resumen_sheet(df_historico, sheet_name="Reporte historico")
    if crono_id is not None:
        row_h = len(df_historico) + 3
        ws_h.write(row_h, 0, "ID Cronograma:", report.styles.total_label)
        ws_h.write(row_h, 1, crono_id, report.styles.total_val)
    
    report.close()

def generar_y_exportar(df_resultados, df_personal, dias_del_bloque, feriados, fecha_inicio, offset_dia, config_turnos, num_semanas, flrs_asignados=None, df_cat_semanas=None, file_name='Cronograma_Enfermeria_UTI.xlsx', crono_id=None):
    if 'Personal' in df_resultados.columns and 'Kinesiologo' not in df_resultados.columns:
        df_resultados['Kinesiologo'] = df_resultados['Personal']
    df_pivot, fechas_unicas = exportar_excel_data_prep(df_resultados, config_turnos)
    df_persona = exportar_excel_vista_personal(df_resultados, df_personal, flrs_asignados)
    exportar_excel(df_pivot, df_persona, fechas_unicas, df_resultados, df_personal, dias_del_bloque, feriados, fecha_inicio, offset_dia, file_name=file_name, df_cat_semanas=df_cat_semanas, crono_id=crono_id)
