import pandas as pd
from datetime import date, timedelta
from database import queries as database
from reportes.generales.base import BaseReport, col_to_letter

def exportar_excel_data_prep(df_resultados, config_turnos, fecha_inicio=None, df_personal=None):
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
            row_n = row.copy(); row_n['Turno'] = "N"; filas_extra.append(row_n)
            indices_a_borrar.append(idx)
        elif row['Turno'] == 'TTN':
            row_t = row.copy(); row_t['Turno'] = "T"; filas_extra.append(row_t)
            row_tn = row.copy(); row_tn['Turno'] = "TN"; filas_extra.append(row_tn)
            indices_a_borrar.append(idx)
            
    df_excel = df_excel.drop(indices_a_borrar)
    if filas_extra:
        df_excel = pd.concat([df_excel, pd.DataFrame(filas_extra)], ignore_index=True)
        
    fechas_originales = sorted([f for f in df_resultados['Fecha'].unique() if not fecha_inicio or f >= fecha_inicio])
    fechas_unicas = sorted(df_excel['Fecha'].unique())
    
    if fechas_originales:
        fecha_limite_exclusiva = (date.fromisoformat(fechas_originales[-1]) + timedelta(days=1)).isoformat()
        fechas_unicas = [f for f in fechas_unicas if (not fecha_inicio or f >= fecha_inicio) and f < fecha_limite_exclusiva]
    
    turnos_ordenados = ["M", "T", "TN", "N"]
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

    nombres_personal = set(df_personal['Nombre'].tolist()) if df_personal is not None else None
    for fecha in fechas_unicas:
        fecha_dt = date.fromisoformat(fecha)
        nombres_lpp = [n for n, r in database.LPP.items() if (nombres_personal is None or n in nombres_personal) and any(date.fromisoformat(i) <= fecha_dt <= date.fromisoformat(f) for i, f in r)]
        fila_lpp[fecha] = "\n".join(nombres_lpp)
        nombres_lar = [n for n, r in database.LAR.items() if (nombres_personal is None or n in nombres_personal) and any(date.fromisoformat(i) <= fecha_dt <= date.fromisoformat(f) for i, f in r)]
        fila_lar[fecha] = "\n".join(nombres_lar)
        nombres_lm = [n for n, r in getattr(database, 'LM', {}).items() if (nombres_personal is None or n in nombres_personal) and any(date.fromisoformat(i) <= fecha_dt <= date.fromisoformat(f) for i, f in r)]
        fila_lm[fecha] = "\n".join(nombres_lm)
        nombres_cm = [n for n, r in getattr(database, 'CM', {}).items() if (nombres_personal is None or n in nombres_personal) and any(date.fromisoformat(i) <= fecha_dt <= date.fromisoformat(f) for i, f in r)]
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
        return 12 if t in ["MT", "TNN", "TTN"] else 6 if t in ["M", "T", "TN", "N"] else 0

    filas = []
    for nombre in nombres:
        fila = {"Enfermero": nombre}
        total_horas_efectivas = 0
        total_horas_nocturnas = 0
        total_f = 0
        dias_licencia = 0
        for fecha in fechas:
            fecha_dt = date.fromisoformat(fecha)
            asig = df_resultados[(df_resultados['Kinesiologo'] == nombre) & (df_resultados['Fecha'] == fecha)]
            if not asig.empty:
                t = asig.iloc[0]['Turno']
                fila[fecha] = t
                total_horas_efectivas += asignar_horas_enf(t)
                if t == "N":
                    total_horas_nocturnas += 6
                elif t == "TNN":
                    total_horas_nocturnas += 8
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
                else: fila[fecha] = "FS"; total_f += 1
        
        dias_periodo = len(fechas)
        horas_licencia = round((144.0 / dias_periodo) * dias_licencia, 1) if dias_periodo > 0 else 0
        
        fila["H. Efectivas"] = total_horas_efectivas
        fila["H. Licencia"] = horas_licencia
        fila["H. Totales"] = total_horas_efectivas + horas_licencia
        fila["H. Nocturnas"] = total_horas_nocturnas
        fila["FS"] = total_f
        filas.append(fila)
        
    return pd.DataFrame(filas).set_index("Enfermero")

def generar_reporte_horas(df_resultados):
    df_reporte_horas = df_resultados.copy()
    def asignar_horas_enf(t):
        return 12 if t in ["MT", "TNN", "TTN"] else 6
    df_reporte_horas['Horas'] = df_reporte_horas['Turno'].apply(asignar_horas_enf)
    horas_por_persona = df_reporte_horas.groupby('Kinesiologo')['Horas'].sum().reset_index()
    reporte_final = horas_por_persona.rename(columns={'Kinesiologo': 'Enfermero', 'Horas': 'Horas Mensuales'})
    return reporte_final.sort_values(by='Horas Mensuales', ascending=False).reset_index(drop=True)

def asignar_horas_enf(t):
    return 12 if t in ["MT", "TNN", "TTN"] else 6 if t in ["M", "T", "TN", "N"] else 0

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
    feriados_trabajados = len(set(g['fecha'] for g in guardias if g['fecha'] in feriados_set))
    
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
    from database.queries import obtener_feriados
    data_feriados = obtener_feriados(servicio_id=2)
    
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

def exportar_excel(df_pivot, df_persona, fechas_unicas, df_resultados, df_personal, dias_del_bloque, feriados, fecha_inicio, offset_dia, file_name='Cronograma_Enfermeria_UTI.xlsx', df_cat_semanas=None, crono_id=None, df_resultados_original=None):
    report = BaseReport(file_name, feriados=feriados, fecha_inicio=fecha_inicio, crono_id=crono_id, servicio_id=2)
    
    # 1. Cronograma
    ws_c = report.generar_cronograma_sheet(df_pivot, fechas_unicas)
    if crono_id is not None:
        row_c = len(df_pivot) + 3
        ws_c.write(row_c, 0, "ID Cronograma:", report.styles.total_label)
        ws_c.write(row_c, 1, crono_id, report.styles.total_val)
    
    # 2. Vista por Personal
    ext_cols = ["H. Efectivas", "H. Licencia", "H. Totales", "H. Nocturnas"]
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
        df_res_semana = df_resultados_original if df_resultados_original is not None else df_resultados
        if not df_res_semana.empty:
            df_res_week = df_res_semana.copy()
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

    num_fechas = len(fechas_unicas)
    end_col_let = col_to_letter(num_fechas)
    
    formulas_vista = {
        "H. Efectivas": f'=(COUNTIF(B{{row}}:{end_col_let}{{row}}, "M") + COUNTIF(B{{row}}:{end_col_let}{{row}}, "T") + COUNTIF(B{{row}}:{end_col_let}{{row}}, "TN") + COUNTIF(B{{row}}:{end_col_let}{{row}}, "N")) * 6 + (COUNTIF(B{{row}}:{end_col_let}{{row}}, "MT") + COUNTIF(B{{row}}:{end_col_let}{{row}}, "TNN") + COUNTIF(B{{row}}:{end_col_let}{{row}}, "TTN")) * 12',
        "H. Licencia": f'=({num_fechas} - (COUNTIF(B{{row}}:{end_col_let}{{row}}, "M") + COUNTIF(B{{row}}:{end_col_let}{{row}}, "T") + COUNTIF(B{{row}}:{end_col_let}{{row}}, "TN") + COUNTIF(B{{row}}:{end_col_let}{{row}}, "N") + COUNTIF(B{{row}}:{end_col_let}{{row}}, "MT") + COUNTIF(B{{row}}:{end_col_let}{{row}}, "TNN") + COUNTIF(B{{row}}:{end_col_let}{{row}}, "TTN") + COUNTIF(B{{row}}:{end_col_let}{{row}}, "F") + COUNTIF(B{{row}}:{end_col_let}{{row}}, "FS") + COUNTIF(B{{row}}:{end_col_let}{{row}}, "FLR") + COUNTIF(B{{row}}:{end_col_let}{{row}}, "FCG"))) * (144.0 / {num_fechas})',
        "H. Totales": "={H_Efectivas}{row} + {H_Licencia}{row}",
        "H. Nocturnas": f'=COUNTIF(B{{row}}:{end_col_let}{{row}}, "N") * 6 + COUNTIF(B{{row}}:{end_col_let}{{row}}, "TNN") * 8'
    }

    def agregar_totales_franja(ws, row_end, range_start=3):
        current_row = row_end + 1
        range_end = row_end
        
        for turno_count in ["M", "T", "TN", "N"]:
            ws.write(current_row, 0, f"TOTAL {turno_count}", report.styles.total_label)
            for col_idx, fecha in enumerate(fechas_unicas):
                col_letter = col_to_letter(col_idx + 1)
                
                if turno_count == "M":
                    formula = f'=COUNTIF({col_letter}{range_start}:{col_letter}{range_end}, "M") + COUNTIF({col_letter}{range_start}:{col_letter}{range_end}, "MT")'
                elif turno_count == "T":
                    formula = f'=COUNTIF({col_letter}{range_start}:{col_letter}{range_end}, "T") + COUNTIF({col_letter}{range_start}:{col_letter}{range_end}, "MT") + COUNTIF({col_letter}{range_start}:{col_letter}{range_end}, "TTN")'
                elif turno_count == "TN":
                    formula = f'=COUNTIF({col_letter}{range_start}:{col_letter}{range_end}, "TN") + COUNTIF({col_letter}{range_start}:{col_letter}{range_end}, "TNN") + COUNTIF({col_letter}{range_start}:{col_letter}{range_end}, "TTN")'
                elif turno_count == "N":
                    formula = f'=COUNTIF({col_letter}{range_start}:{col_letter}{range_end}, "N") + COUNTIF({col_letter}{range_start}:{col_letter}{range_end}, "TNN")'
                
                is_sep = report._es_fin_de_semana_sep(fecha)
                ws.write_formula(current_row, col_idx + 1, formula, report.styles.total_val_week if is_sep else report.styles.total_val)
            current_row += 1
            
        if crono_id is not None:
            current_row += 2
            ws.write(current_row, 0, "ID Cronograma:", report.styles.total_label)
            ws.write(current_row, 1, crono_id, report.styles.total_val)
            
        return current_row

    # Vista Personal Reporte (con reporte de horas)
    ws_p_rep, row_end_rep = report.generar_vista_personal_sheet(df_persona, fechas_unicas, extension_columns=ext_cols, label_personal="ENFERMERO", sheet_name='Vista Personal Reporte', formulas=formulas_vista)
    
    # Vista Personal (sin reporte, francos renombrados a FS)
    ext_cols_sin = ["H. Efectivas", "H. Licencia", "H. Totales", "H. Nocturnas"]
    ws_p_sin, row_end_sin = report.generar_vista_personal_sheet(df_persona, fechas_unicas, extension_columns=ext_cols_sin, label_personal="ENFERMERO", sheet_name='Vista Personal', renombrar_francos=True, formulas=formulas_vista)
    
    # --- TOTALES POR FRANJA ---
    agregar_totales_franja(ws_p_rep, row_end_rep, range_start=3)
    crono_start_row = agregar_totales_franja(ws_p_sin, row_end_sin, range_start=6)

    # -------------------------------------------------------------------------
    # VISTA DE CRONOGRAMA DINÁMICA (en la misma hoja "Vista Personal")
    # -------------------------------------------------------------------------
    title_fmt = report.workbook.add_format({
        'bold': True, 'font_size': 12, 'bg_color': '#BDD7EE',
        'align': 'center', 'valign': 'vcenter', 'border': 1
    })

    crono_title_row = crono_start_row + 2
    ws_p_sin.merge_range(crono_title_row, 0, crono_title_row, len(fechas_unicas), "CRONOGRAMA (DINÁMICO)", title_fmt)
    ws_p_sin.set_row(crono_title_row, 25)

    h1_row = crono_title_row + 2
    h2_row = crono_title_row + 3
    ws_p_sin.merge_range(h1_row, 0, h2_row, 0, "TURNO", report.styles.header_blue)

    for col_idx, fecha in enumerate(fechas_unicas):
        dt = date.fromisoformat(fecha)
        sigla = report.siglas_dias[dt.weekday()]
        dia_num = f"{dt.day}/{dt.month}"
        is_sep = report._es_fin_de_semana_sep(fecha)
        is_dark = (dt.weekday() >= 5) or (fecha in report.feriados)
        if is_dark:
            fmt_h1 = report.styles.header_dark_blue_week if is_sep else report.styles.header_dark_blue
            fmt_h2 = report.styles.header_dark_light_week if is_sep else report.styles.header_dark_light
        else:
            fmt_h1 = report.styles.header_blue_week if is_sep else report.styles.header_blue
            fmt_h2 = report.styles.header_light_week if is_sep else report.styles.header_light
        ws_p_sin.write(h1_row, col_idx + 1, sigla, fmt_h1)
        ws_p_sin.write(h2_row, col_idx + 1, dia_num, fmt_h2)

    # Helpers para el cronograma dinámico
    BUFFER_EXTRA = 3  # filas adicionales por turno para acomodar ediciones del usuario
    ref_last = row_end_sin  # último Excel row (1-indexed) con datos de personal
    ref_start = 6

    def _fmt_crono_turno(base_turno, is_sep):
        """Formato celda cronograma: color de turno, font_size=8."""
        color = report.styles.shift_colors.get(base_turno, '#FFFFFF')
        d = {'bg_color': color, 'border': 1, 'align': 'center',
             'valign': 'vcenter', 'font_size': 8, 'text_wrap': True}
        if is_sep:
            d['right'] = 5
        return report.workbook.add_format(d)

    def _build_cond(base_turno, cl, rl):
        """Condición booleana para SMALL+IF según turno base."""
        if base_turno == "M":
            return f'({cl}${ref_start}:{cl}${rl}="M")+({cl}${ref_start}:{cl}${rl}="MT")>0'
        elif base_turno == "T":
            return f'({cl}${ref_start}:{cl}${rl}="T")+({cl}${ref_start}:{cl}${rl}="MT")+({cl}${ref_start}:{cl}${rl}="TTN")>0'
        elif base_turno == "TN":
            return f'({cl}${ref_start}:{cl}${rl}="TN")+({cl}${ref_start}:{cl}${rl}="TNN")+({cl}${ref_start}:{cl}${rl}="TTN")>0'
        elif base_turno == "N":
            return f'({cl}${ref_start}:{cl}${rl}="N")+({cl}${ref_start}:{cl}${rl}="TNN")>0'
        else:
            return f'{cl}${ref_start}:{cl}${rl}="{base_turno}"'

    def _write_turno_row(row, base_turno, occ):
        """Escribe una fila del cronograma dinámico mostrando solo apellido."""
        ws_p_sin.write(row, 0, base_turno, report.styles.header_blue)
        for col_idx, fecha in enumerate(fechas_unicas):
            is_sep = report._es_fin_de_semana_sep(fecha)
            cl = col_to_letter(col_idx + 1)
            cond = _build_cond(base_turno, cl, ref_last)
            # Inner: INDEX(..., SMALL(IF(cond, ROW-offset), occ))
            inner = (
                f'INDEX($A${ref_start}:$A${ref_last},'
                f'SMALL(IF({cond},'
                f'ROW($A${ref_start}:$A${ref_last})-ROW($A${ref_start})+1),{occ}))'
            )
            # Apellido: texto antes de la primera coma (o nombre completo si no hay coma)
            formula = (
                f'=IFERROR(TRIM(LEFT({inner},'
                f'FIND(",",{inner}&",")-1)),"")'
            )
            fmt = _fmt_crono_turno(base_turno, is_sep)
            ws_p_sin.write_array_formula(row, col_idx + 1, row, col_idx + 1, formula, fmt)
        ws_p_sin.set_row(row, 20)

    seen_counts = {"M": 0, "T": 0, "TN": 0, "N": 0}
    curr_crono_row = h2_row + 1
    i_piv = 0
    n_pivot = len(df_pivot)

    while i_piv < n_pivot:
        turno_label = df_pivot.index[i_piv]

        if str(turno_label).strip() == "":
            # Fila espaciadora
            fmt_sp = report.workbook.add_format({'bg_color': '#FFFFFF', 'border': 0})
            ws_p_sin.write(curr_crono_row, 0, "", fmt_sp)
            for col_idx in range(len(fechas_unicas)):
                ws_p_sin.write(curr_crono_row, col_idx + 1, "", fmt_sp)
            ws_p_sin.set_row(curr_crono_row, 15)
            curr_crono_row += 1
            i_piv += 1

        elif turno_label in ["LPP", "LAR", "LM", "CM"]:
            # Fila de licencias
            ws_p_sin.write(curr_crono_row, 0, turno_label, report.styles.header_blue)
            for col_idx, fecha in enumerate(fechas_unicas):
                is_sep = report._es_fin_de_semana_sep(fecha)
                cl = col_to_letter(col_idx + 1)
                fmt = report.styles.grey_cell_week if is_sep else report.styles.grey_cell
                formula = (
                    f'=IFERROR(TEXTJOIN(CHAR(10),TRUE,'
                    f'IF({cl}${ref_start}:{cl}${ref_last}="{turno_label}",'
                    f'$A${ref_start}:$A${ref_last},"")),"")'
                )
                ws_p_sin.write_array_formula(
                    curr_crono_row, col_idx + 1,
                    curr_crono_row, col_idx + 1,
                    formula, fmt
                )
            ws_p_sin.set_row(curr_crono_row, 30)
            curr_crono_row += 1
            i_piv += 1

        else:
            # Grupo de turno (M, T, TN, N)
            base_turno = str(turno_label).split('_')[0]
            # Escribir todas las filas df_pivot del grupo
            while (i_piv < n_pivot
                   and str(df_pivot.index[i_piv]).strip() != ""
                   and df_pivot.index[i_piv] not in ["LPP", "LAR", "LM", "CM"]
                   and str(df_pivot.index[i_piv]).split('_')[0] == base_turno):
                seen_counts[base_turno] += 1
                _write_turno_row(curr_crono_row, base_turno, seen_counts[base_turno])
                curr_crono_row += 1
                i_piv += 1
            # Filas buffer adicionales
            for extra in range(1, BUFFER_EXTRA + 1):
                _write_turno_row(curr_crono_row, base_turno, seen_counts[base_turno] + extra)
                curr_crono_row += 1

    # -------------------------------------------------------------------------
    # DOS LÍNEAS DIVISORIAS GRUESAS
    # -------------------------------------------------------------------------
    divider_row = curr_crono_row + 1
    thick_fmt = report.workbook.add_format({'bottom': 5})
    last_col = len(fechas_unicas) + 6
    for c in range(last_col + 1):
        ws_p_sin.write(divider_row, c, "", thick_fmt)
        ws_p_sin.write(divider_row + 1, c, "", thick_fmt)

    # -------------------------------------------------------------------------
    # VISTA PERSONAL ORIGINAL (Estática / Histórico)
    # -------------------------------------------------------------------------
    orig_start_row = divider_row + 3
    
    # Escribir encabezado institucional
    title_bold = report.workbook.add_format({'bold': True, 'font_size': 11})
    ws_p_sin.write(orig_start_row, 0, "HOSPITAL CENTRAL RAMON CARRILLO", title_bold)
    ws_p_sin.write(orig_start_row + 1, 0, "DEPARTAMENTO DE ENFERMERÍA", title_bold)
    ws_p_sin.write(orig_start_row + 2, 0, "PLANILLA DE ROTACION: ENFERMERÍA AREA CRITICA", title_bold)
    
    # Mes / Año dinámicos
    MESES = {
        1: "ENERO", 2: "FEBRERO", 3: "MARZO", 4: "ABRIL",
        5: "MAYO", 6: "JUNIO", 7: "JULIO", 8: "AGOSTO",
        9: "SEPTIEMBRE", 10: "OCTUBRE", 11: "NOVIEMBRE", 12: "DICIEMBRE"
    }
    dt_start = date.fromisoformat(fecha_inicio)
    mes_str = MESES[dt_start.month]
    anio_str = str(dt_start.year)
    mes_anio_text = f"MES:   {mes_str}     AÑO:     {anio_str}"
    ws_p_sin.write(orig_start_row + 2, 14, mes_anio_text, title_bold)

    orig_h1_row = orig_start_row + 3
    orig_h2_row = orig_start_row + 4
    ws_p_sin.merge_range(orig_h1_row, 0, orig_h2_row, 0, "ENFERMERO", report.styles.header_blue)

    for col_idx, fecha in enumerate(fechas_unicas):
        dt = date.fromisoformat(fecha)
        sigla = report.siglas_dias[dt.weekday()]
        dia_num = str(dt.day)
        is_sep = report._es_fin_de_semana_sep(fecha)
        is_dark = (dt.weekday() >= 5) or (fecha in report.feriados)
        if is_dark:
            fmt_h1 = report.styles.header_dark_blue_week if is_sep else report.styles.header_dark_blue
            fmt_h2 = report.styles.header_dark_light_week if is_sep else report.styles.header_dark_light
        else:
            fmt_h1 = report.styles.header_blue_week if is_sep else report.styles.header_blue
            fmt_h2 = report.styles.header_light_week if is_sep else report.styles.header_light
        ws_p_sin.write(orig_h1_row, col_idx + 1, sigla, fmt_h1)
        ws_p_sin.write(orig_h2_row, col_idx + 1, dia_num, fmt_h2)

    col_offset_orig = len(fechas_unicas) + 2
    for i, col_name in enumerate(ext_cols_sin):
        ws_p_sin.merge_range(orig_h1_row, col_offset_orig + i, orig_h2_row, col_offset_orig + i, col_name, report.styles.header_blue)

    # Formatos especiales para la vista original (finde/feriado)
    _fmt_finde = report.workbook.add_format({'bg_color': '#E8EEF5', 'border': 1, 'align': 'center', 'valign': 'vcenter', 'font_size': 9, 'text_wrap': True})
    _fmt_finde_wk = report.workbook.add_format({'bg_color': '#E8EEF5', 'border': 1, 'right': 5, 'align': 'center', 'valign': 'vcenter', 'font_size': 9, 'text_wrap': True})
    _fmt_turno_finde = report.workbook.add_format({'bg_color': '#E8EEF5', 'border': 1, 'bold': True, 'align': 'center', 'valign': 'vcenter', 'font_size': 9, 'text_wrap': True})
    _fmt_turno_finde_wk = report.workbook.add_format({'bg_color': '#E8EEF5', 'border': 1, 'right': 5, 'bold': True, 'align': 'center', 'valign': 'vcenter', 'font_size': 9, 'text_wrap': True})
    _fmt_feriado = report.workbook.add_format({'bg_color': '#FADBD8', 'border': 1, 'align': 'center', 'valign': 'vcenter', 'font_size': 9, 'text_wrap': True})
    _fmt_feriado_wk = report.workbook.add_format({'bg_color': '#FADBD8', 'border': 1, 'right': 5, 'align': 'center', 'valign': 'vcenter', 'font_size': 9, 'text_wrap': True})
    _fmt_turno_feriado = report.workbook.add_format({'bg_color': '#FADBD8', 'border': 1, 'bold': True, 'align': 'center', 'valign': 'vcenter', 'font_size': 9, 'text_wrap': True})
    _fmt_turno_feriado_wk = report.workbook.add_format({'bg_color': '#FADBD8', 'border': 1, 'right': 5, 'bold': True, 'align': 'center', 'valign': 'vcenter', 'font_size': 9, 'text_wrap': True})

    orig_data_start_row = orig_h2_row + 1
    row_ex_orig = orig_data_start_row

    for nombre, row_data in df_persona.iterrows():
        ws_p_sin.write(row_ex_orig, 0, nombre, report.styles.name_cell)

        fechas_vals_orig = []
        for col_idx, fecha in enumerate(fechas_unicas):
            val = row_data[fecha]
            if pd.isna(val) or str(val).lower() == 'nan':
                val = ""
            val = str(val)
            if val in ["F", "FLR"]:
                val = "FS"
            fechas_vals_orig.append((col_idx, fecha, val))

        i_f = 0
        while i_f < len(fechas_unicas):
            col_idx, fecha, val = fechas_vals_orig[i_f]
            if val in ["LAR", "LPP", "LM", "CM"]:
                j_f = i_f + 1
                while j_f < len(fechas_unicas) and fechas_vals_orig[j_f][2] == val:
                    j_f += 1
                ultimo_fecha = fechas_vals_orig[j_f - 1][1]
                ultimo_is_sep = report._es_fin_de_semana_sep(ultimo_fecha)
                fmt_lic = report.styles.grey_cell_week if ultimo_is_sep else report.styles.grey_cell
                if i_f + 1 < j_f:
                    ws_p_sin.merge_range(row_ex_orig, i_f + 1, row_ex_orig, j_f, val, fmt_lic)
                else:
                    ws_p_sin.write(row_ex_orig, i_f + 1, val, fmt_lic)
                i_f = j_f
            else:
                dt = date.fromisoformat(fecha)
                is_sep = report._es_fin_de_semana_sep(fecha)
                is_weekend = (dt.weekday() >= 5)
                is_holiday = (fecha in report.feriados)
                if is_holiday:
                    fmt = _fmt_turno_feriado_wk if (is_sep and val not in ["FS", "FCG"]) else (_fmt_feriado_wk if is_sep else (_fmt_turno_feriado if val not in ["FS", "FCG"] else _fmt_feriado))
                elif is_weekend:
                    fmt = _fmt_turno_finde_wk if (is_sep and val not in ["FS", "FCG"]) else (_fmt_finde_wk if is_sep else (_fmt_turno_finde if val not in ["FS", "FCG"] else _fmt_finde))
                else:
                    fmt = report.styles.cell_week if is_sep else report.styles.cell
                ws_p_sin.write(row_ex_orig, col_idx + 1, val, fmt)
                i_f += 1

        # Escribir columnas de extensión estáticas
        for i_ext, col_name in enumerate(ext_cols_sin):
            val_to_write = row_data[col_name]
            ws_p_sin.write(row_ex_orig, col_offset_orig + i_ext, val_to_write, report.styles.cell)

        row_ex_orig += 1

    # Totales estáticos para la vista original
    orig_1idx_start = orig_data_start_row + 1
    orig_1idx_end = row_ex_orig
    curr_tot = row_ex_orig + 1
    for turno_count in ["M", "T", "TN", "N"]:
        ws_p_sin.write(curr_tot, 0, f"TOTAL {turno_count}", report.styles.total_label)
        for col_idx, fecha in enumerate(fechas_unicas):
            col_letter = col_to_letter(col_idx + 1)
            if turno_count == "M":
                formula = f'=COUNTIF({col_letter}{orig_1idx_start}:{col_letter}{orig_1idx_end},"M")+COUNTIF({col_letter}{orig_1idx_start}:{col_letter}{orig_1idx_end},"MT")'
            elif turno_count == "T":
                formula = f'=COUNTIF({col_letter}{orig_1idx_start}:{col_letter}{orig_1idx_end},"T")+COUNTIF({col_letter}{orig_1idx_start}:{col_letter}{orig_1idx_end},"MT")+COUNTIF({col_letter}{orig_1idx_start}:{col_letter}{orig_1idx_end},"TTN")'
            elif turno_count == "TN":
                formula = f'=COUNTIF({col_letter}{orig_1idx_start}:{col_letter}{orig_1idx_end},"TN")+COUNTIF({col_letter}{orig_1idx_start}:{col_letter}{orig_1idx_end},"TNN")+COUNTIF({col_letter}{orig_1idx_start}:{col_letter}{orig_1idx_end},"TTN")'
            elif turno_count == "N":
                formula = f'=COUNTIF({col_letter}{orig_1idx_start}:{col_letter}{orig_1idx_end},"N")+COUNTIF({col_letter}{orig_1idx_start}:{col_letter}{orig_1idx_end},"TNN")'
            is_sep = report._es_fin_de_semana_sep(fecha)
            ws_p_sin.write_formula(curr_tot, col_idx + 1, formula, report.styles.total_val_week if is_sep else report.styles.total_val)
        curr_tot += 1


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

def generar_y_exportar(df_resultados, df_personal, dias_del_bloque, feriados, fecha_inicio, offset_dia, config_turnos, num_semanas, flrs_asignados=None, df_cat_semanas=None, file_name=None, crono_id=None):
    if not file_name:
        from utils import obtener_nombre_archivo
        file_name = obtener_nombre_archivo('Cronograma_Enfermeria_UTI.xlsx', fecha_inicio)
    if 'Personal' in df_resultados.columns and 'Kinesiologo' not in df_resultados.columns:
        df_resultados['Kinesiologo'] = df_resultados['Personal']
    
    # Cargar guardias de ayer para considerar la parte N de los turnos de 12h (como TNN)
    fecha_inicio_dt = date.fromisoformat(fecha_inicio)
    fecha_ayer = (fecha_inicio_dt - timedelta(days=1)).isoformat()
    
    from database.connection import get_connection
    guardias_ayer = []
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT g.fecha, g.turno, g.nombre
                FROM guardias g
                JOIN personal p ON g.nombre = p.nombre
                JOIN cronogramas c ON g.cronograma_id = c.id
                WHERE g.fecha = ? AND p.servicio_id = 2 AND c.estado = 'aprobado'
            """, (fecha_ayer,))
            for f, t, n in cursor.fetchall():
                guardias_ayer.append({
                    "Fecha": f,
                    "Dia_Semana": "",
                    "Turno": t,
                    "Personal": n,
                    "Kinesiologo": n
                })
    except Exception as e:
        print(f"[reportes] Error al cargar guardias del día anterior: {e}")
        
    df_resultados_con_ayer = df_resultados.copy()
    if guardias_ayer:
        df_resultados_con_ayer = pd.concat([df_resultados_con_ayer, pd.DataFrame(guardias_ayer)], ignore_index=True)

    df_pivot, fechas_unicas = exportar_excel_data_prep(df_resultados_con_ayer, config_turnos, fecha_inicio, df_personal=df_personal)
    df_persona = exportar_excel_vista_personal(df_resultados, df_personal, flrs_asignados)
    exportar_excel(df_pivot, df_persona, fechas_unicas, df_resultados_con_ayer, df_personal, dias_del_bloque, feriados, fecha_inicio, offset_dia, file_name=file_name, df_cat_semanas=df_cat_semanas, crono_id=crono_id, df_resultados_original=df_resultados)
