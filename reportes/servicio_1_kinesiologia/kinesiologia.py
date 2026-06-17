import pandas as pd
from datetime import date, timedelta
from database import queries as database
from reportes.generales.base import BaseReport

def exportar_excel_data_prep(df_resultados, config_turnos, df_personal=None):
    # --- PIVOTEAR EL CRONOGRAMA ---
    df_excel = df_resultados.copy()
    
    # Desdoblar turnos "Dia_" solo para la vista (desactivado a solicitud para conservar fila Día)
    # filas_extra = []
    # indices_a_borrar = []
    # for idx, row in df_excel.iterrows():
    #     if row['Turno'].startswith('Dia_'):
    #         suffix = row['Turno'].replace('Dia_', '')
    #         row_m = row.copy(); row_m['Turno'] = f"Mañana_{suffix}"; filas_extra.append(row_m)
    #         row_t = row.copy(); row_t['Turno'] = f"Tarde_{suffix}"; filas_extra.append(row_t)
    #         indices_a_borrar.append(idx)
    #         
    # df_excel = df_excel.drop(indices_a_borrar)
    # if filas_extra:
    #     df_excel = pd.concat([df_excel, pd.DataFrame(filas_extra)], ignore_index=True)
        
    fechas_unicas = sorted(df_excel['Fecha'].unique().tolist())
    turnos_ordenados = []
    for tipo in ["Semana", "Finde_Feriado"]:
        for t in config_turnos.get(tipo, {}).keys():
            if t not in turnos_ordenados:
                turnos_ordenados.append(t)
                
    # Ordenar los turnos para agrupar Mañana -> Día -> Tarde -> Noche, y luego por sector (UTI -> UCO -> especial)
    def orden_turno(t):
        t_lower = t.lower()
        if "mañana" in t_lower or "maana" in t_lower:
            prioridad_tipo = 1
        elif "dia" in t_lower:
            prioridad_tipo = 2
        elif "tarde" in t_lower:
            prioridad_tipo = 3
        elif "noche" in t_lower:
            prioridad_tipo = 4
        else:
            prioridad_tipo = 5
            
        if "uti" in t_lower:
            prioridad_sector = 1
        elif "uco" in t_lower:
            prioridad_sector = 2
        elif "especial" in t_lower:
            prioridad_sector = 3
        else:
            prioridad_sector = 4
            
        return (prioridad_tipo, prioridad_sector)
        
    turnos_ordenados.sort(key=orden_turno)
                
    filas_excel = []
    
    # Jerarquía para ordenamiento
    rows_p = database.get_connection().execute("SELECT nombre, rol FROM personal").fetchall()
    jerarquia = {}
    rol_orden = {"Jefe": 1, "Coordinador": 2, "Rotativo": 3, "Nocturno": 4}
    for n, r in rows_p: jerarquia[n] = rol_orden.get(r, 100)

    for turno_label in turnos_ordenados:
        df_turno = df_excel[df_excel['Turno'] == turno_label]
        max_p = 0
        for f in fechas_unicas:
            c = len(df_turno[df_turno['Fecha'] == f])
            if c > max_p: max_p = c
        
        if max_p == 0: continue

        for i in range(max_p):
            fila = {"Turno": turno_label}
            for f in fechas_unicas:
                pers_dia = df_turno[df_turno['Fecha'] == f].sort_values(
                    by='Personal', key=lambda x: x.map(lambda n: jerarquia.get(n, 100))
                )['Personal'].tolist()
                fila[f] = pers_dia[i].split(',')[0].strip() if i < len(pers_dia) else ""
            filas_excel.append(fila)

    # Licencias
    filas_excel.append({"Turno": "  "}) 
    fila_lpp = {"Turno": "LPP"}
    fila_lar = {"Turno": "LAR"}
    fila_lm = {"Turno": "LM"}
    fila_cm = {"Turno": "CM"}

    nombres_personal = set(df_personal['Nombre'].tolist()) if df_personal is not None else None
    for fecha in fechas_unicas:
        fecha_dt = date.fromisoformat(fecha)
        nombres_lpp = [n.split(',')[0].strip() for n, r in database.LPP.items() if (nombres_personal is None or n in nombres_personal) and any(date.fromisoformat(i) <= fecha_dt <= date.fromisoformat(f) for i, f in r)]
        fila_lpp[fecha] = "\n".join(nombres_lpp)
        nombres_lar = [n.split(',')[0].strip() for n, r in database.LAR.items() if (nombres_personal is None or n in nombres_personal) and any(date.fromisoformat(i) <= fecha_dt <= date.fromisoformat(f) for i, f in r)]
        fila_lar[fecha] = "\n".join(nombres_lar)
        nombres_lm = [n.split(',')[0].strip() for n, r in getattr(database, 'LM', {}).items() if (nombres_personal is None or n in nombres_personal) and any(date.fromisoformat(i) <= fecha_dt <= date.fromisoformat(f) for i, f in r)]
        fila_lm[fecha] = "\n".join(nombres_lm)
        nombres_cm = [n.split(',')[0].strip() for n, r in getattr(database, 'CM', {}).items() if (nombres_personal is None or n in nombres_personal) and any(date.fromisoformat(i) <= fecha_dt <= date.fromisoformat(f) for i, f in r)]
        fila_cm[fecha] = "\n".join(nombres_cm)

    filas_excel.append(fila_lpp)
    filas_excel.append(fila_lar)
    filas_excel.append(fila_lm)
    filas_excel.append(fila_cm)

    df_pivot = pd.DataFrame(filas_excel).set_index("Turno")
    return df_pivot, fechas_unicas

def mapear_turno_a_inicial(turno_raw):
    if not turno_raw:
        return ""
    # Normalizar posibles caracteres
    t = str(turno_raw).replace("Maana", "Mañana")
    
    if t.startswith("Mañana_UTI"):
        return "MUT"
    elif t.startswith("Tarde_UTI"):
        return "TUT"
    elif t.startswith("Mañana_UCO"):
        return "MUC"
    elif t.startswith("Tarde_UCO"):
        return "TUC"
    elif t.startswith("Mañana_especial"):
        return "ME"
    elif t.startswith("Tarde_especial"):
        return "TE"
    elif t.startswith("Noche"):
        return "N"
    elif t.startswith("Dia_UTI"):
        return "DUT"
    elif t.startswith("Dia_UCO"):
        return "DUC"
    elif t.startswith("Dia_especial"):
        return "DE"
    return t

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
            
    col_nombre = 'Personal' if 'Personal' in df_resultados.columns else 'Kinesiologo'
    
    # Agrupar fechas por semana calendario (de lunes a domingo) para calcular FS y seguimientos
    semanas = {}
    for fecha in fechas:
        fecha_dt = date.fromisoformat(fecha)
        lunes = fecha_dt - timedelta(days=fecha_dt.weekday())
        semanas.setdefault(lunes.isoformat(), []).append(fecha_dt)
        
    filas = []
    for nombre in nombres:
        fila = {col_nombre: nombre}
        total_horas_efectivas = 0
        dias_licencia = 0
        fechas_trabajadas = set()
        noches_mes = 0
        
        for fecha in fechas:
            asig = df_resultados[(df_resultados[col_nombre] == nombre) & (df_resultados['Fecha'] == fecha)]
            if not asig.empty:
                t = asig.iloc[0]['Turno']
                fila[fecha] = mapear_turno_a_inicial(t)
                total_horas_efectivas += asignar_horas_base(t)
                fechas_trabajadas.add(fecha)
                if t.startswith("Noche") or "Noche" in t:
                    noches_mes += 1
            else:
                fecha_dt = date.fromisoformat(fecha)
                es_flr = any(fi <= fecha_dt <= ff for fi, ff in mapa_flrs.get(nombre, []))
                es_lar = any(date.fromisoformat(i) <= fecha_dt <= date.fromisoformat(f) for i, f in database.LAR.get(nombre, []))
                es_lpp = any(date.fromisoformat(i) <= fecha_dt <= date.fromisoformat(f) for i, f in database.LPP.get(nombre, []))
                es_lm = any(date.fromisoformat(i) <= fecha_dt <= date.fromisoformat(f) for i, f in getattr(database, 'LM', {}).get(nombre, []))
                es_cm = any(date.fromisoformat(i) <= fecha_dt <= date.fromisoformat(f) for i, f in getattr(database, 'CM', {}).get(nombre, []))
                if es_flr:
                    fila[fecha] = "FLR"
                elif es_lar:
                    fila[fecha] = "LAR"
                    dias_licencia += 1
                elif es_lpp:
                    fila[fecha] = "LPP"
                    dias_licencia += 1
                elif es_lm:
                    fila[fecha] = "LM"
                    dias_licencia += 1
                elif es_cm:
                    fila[fecha] = "CM"
                    dias_licencia += 1
                else:
                    fila[fecha] = "F"
                    
        # Calcular Horas lic y Horas totales
        p_row = df_personal[df_personal['Nombre'] == nombre]
        if not p_row.empty:
            horas_reg = p_row.iloc[0].get('horas_mensuales_reglamentarias', 144.0)
            if pd.isna(horas_reg) or horas_reg is None:
                horas_reg = 144.0
        else:
            horas_reg = 144.0
            
        dias_periodo = len(fechas)
        horas_lic = round((horas_reg / dias_periodo) * dias_licencia, 1) if dias_periodo > 0 else 0
        horas_totales = total_horas_efectivas + horas_lic
        
        # Calcular Fines de Semana Completos (FS) y Medios (1/2 FS)
        fs_completos = 0
        fs_medios = 0
        for lunes_str, dias_sem in semanas.items():
            sats = [d for d in dias_sem if d.weekday() == 5]
            suns = [d for d in dias_sem if d.weekday() == 6]
            if not sats or not suns:
                continue
            sat_str = sats[0].isoformat()
            sun_str = suns[0].isoformat()
            
            trabajo_sat = sat_str in fechas_trabajadas
            trabajo_sun = sun_str in fechas_trabajadas
            
            if trabajo_sat and trabajo_sun:
                fs_completos += 1
            elif trabajo_sat or trabajo_sun:
                fs_medios += 1
                
        # Calcular seguimientos a la mañana (Seg M) y a la tarde (Seg T)
        # Se cuenta +1 por cada semana (de lunes a viernes) en la que trabaje >= 4 veces en el mismo turno
        # Un turno "Dia_" (ej: Dia_UTI, Dia_UCO) cuenta como mañana y tarde.
        seg_m = 0
        seg_t = 0
        for lunes_str, dias_sem in semanas.items():
            fechas_lv = [d.isoformat() for d in dias_sem if d.weekday() < 5]
            df_sem_lv = df_resultados[(df_resultados[col_nombre] == nombre) & (df_resultados['Fecha'].isin(fechas_lv))]
            if not df_sem_lv.empty:
                turnos_semana = {}
                for _, row_g in df_sem_lv.iterrows():
                    t = row_g['Turno']
                    if t.startswith('Dia_'):
                        suffix = t.replace('Dia_', '')
                        t_m = f"Mañana_{suffix}"
                        t_t = f"Tarde_{suffix}"
                        turnos_semana[t_m] = turnos_semana.get(t_m, 0) + 1
                        turnos_semana[t_t] = turnos_semana.get(t_t, 0) + 1
                    else:
                        turnos_semana[t] = turnos_semana.get(t, 0) + 1
                
                for t, cnt in turnos_semana.items():
                    if cnt >= 4:
                        t_lower = str(t).lower()
                        if "mañana" in t_lower or "maana" in t_lower:
                            seg_m += 1
                        elif "tarde" in t_lower:
                            seg_t += 1
                            
        fila["Horas efectivas"] = total_horas_efectivas
        fila["Horas lic"] = horas_lic
        fila["Horas totales"] = horas_totales
        fila["Seg M"] = seg_m
        fila["Seg T"] = seg_t
        fila["FS"] = fs_completos
        fila["1/2 FS"] = fs_medios
        fila["N"] = noches_mes
        
        filas.append(fila)
        
    return pd.DataFrame(filas).set_index(col_nombre)

from reportes.generales.base import asignar_horas_base

def generar_reporte_horas_completo(df_resultados, df_personal, dias_del_bloque, feriados, fecha_inicio, offset_dia, num_semanas):
    df_reporte_horas = df_resultados.copy()
    df_reporte_horas['Horas'] = df_reporte_horas['Turno'].apply(asignar_horas_base)
    horas_por_persona = df_reporte_horas.groupby('Personal')['Horas'].sum().reset_index()
    
    fecha_inicio_dt = pd.to_datetime(fecha_inicio)
    resultados_fl = []
    for _, persona in df_personal.iterrows():
        nombre = persona['Nombre']
        dias_bloqueados = set()
        for lics in [database.LPP, database.LAR, getattr(database, 'LM', {}), getattr(database, 'CM', {})]:
            for (ini_s, fin_s) in lics.get(nombre, []):
                ini_dt = pd.to_datetime(ini_s); fin_dt = pd.to_datetime(fin_s)
                for d in range((fin_dt - ini_dt).days + 1):
                    fecha_iter = ini_dt + pd.Timedelta(days=d)
                    delta = (fecha_iter - fecha_inicio_dt).days
                    if 0 <= delta < dias_del_bloque: dias_bloqueados.add(delta)

        col_nombre = 'Personal' if 'Personal' in df_resultados.columns else 'Kinesiologo'
        fechas_trabajadas = df_resultados[df_resultados['Personal'] == nombre]['Fecha'].tolist()
        bloques = []; bloque_actual = []
        for d in range(dias_del_bloque):
            if d in dias_bloqueados:
                if bloque_actual: bloques.append(bloque_actual); bloque_actual = []
                continue
            es_f = ((d + offset_dia) % 7) >= 5 or d in feriados
            if es_f: bloque_actual.append(d)
            else:
                if bloque_actual: bloques.append(bloque_actual); bloque_actual = []
        if bloque_actual: bloques.append(bloque_actual)

        f_trab_actual = 0; f_hab_actual = 0
        for sem in range(num_semanas):
            s = sem * 7 + (5 - offset_dia) % 7; dom = sem * 7 + (6 - offset_dia) % 7
            if s not in dias_bloqueados and dom not in dias_bloqueados: f_hab_actual += 1
            f_s = (fecha_inicio_dt + pd.Timedelta(days=s)).strftime("%Y-%m-%d")
            f_dom = (fecha_inicio_dt + pd.Timedelta(days=dom)).strftime("%Y-%m-%d")
            if f_s in fechas_trabajadas or f_dom in fechas_trabajadas: f_trab_actual += 1

        fl_3_libres = 0; fl_4_libres = 0
        for bloque in bloques:
            fechas_bloque = [(fecha_inicio_dt + pd.Timedelta(days=d)).strftime("%Y-%m-%d") for d in bloque]
            if not any(f in fechas_trabajadas for f in fechas_bloque):
                if len(bloque) == 3: fl_3_libres += 1
                elif len(bloque) >= 4: fl_4_libres += 1
                    
        horas_acum = persona.get('Horas_Anuales_Previas', 0) + horas_por_persona[horas_por_persona['Personal'] == nombre]['Horas'].sum()
        f_trab_total = persona.get('Findes_Semanas_Previos', 0) + f_trab_actual
        f_hab_total = persona.get('Findes_Habiles_Previos', 10) + f_hab_actual
        indice_carga = round((f_trab_total / f_hab_total) * 100, 1) if f_hab_total > 0 else 0

        resultados_fl.append({
            'Personal': nombre, 'Horas_Anuales_Total': horas_acum,
            'Findes_Actual_Trab': f_trab_actual, 'Findes_Actual_Hab': f_hab_actual,
            'Findes_Trab_Total': f_trab_total, 'Findes_Hab_Total': f_hab_total,
            'Indice_Carga_Finde': f"{indice_carga}%",
            'FL3_Total_Acum': persona.get('Findes_Largos_3_Previos', 0) + fl_3_libres,
            'FL4_Total_Acum': persona.get('Findes_Largos_4_Previos', 0) + fl_4_libres
        })
        
    df_fl = pd.DataFrame(resultados_fl)
    reporte_final = pd.merge(horas_por_persona, df_fl, on='Personal', how='left')
    return reporte_final.rename(columns={
        'Horas': 'H. Actual', 'Horas_Anuales_Total': 'H. Anual',
        'Findes_Actual_Trab': 'FS Act (T)', 'Findes_Actual_Hab': 'FS Act (H)',
        'Findes_Trab_Total': 'Acum (T)', 'Findes_Hab_Total': 'Acum (H)',
        'Indice_Carga_Finde': 'Carga %', 'FL3_Total_Acum': 'FL3 Acum', 'FL4_Total_Acum': 'FL4 Acum'
    }).sort_values(by='H. Actual', ascending=False).reset_index(drop=True)

def calcular_totales_por_turno(df_resultados, fechas_unicas):
    totales_m = {}
    totales_t = {}
    totales_n = {}
    for f in fechas_unicas:
        df_f = df_resultados[df_resultados['Fecha'] == f]
        cant_m = df_f[df_f['Turno'].str.contains('Mañana|Maana|Dia', case=False, na=False)].shape[0]
        cant_t = df_f[df_f['Turno'].str.contains('Tarde|Dia', case=False, na=False)].shape[0]
        cant_n = df_f[df_f['Turno'].str.contains('Noche', case=False, na=False)].shape[0]
        totales_m[f] = cant_m
        totales_t[f] = cant_t
        totales_n[f] = cant_n
    return totales_m, totales_t, totales_n

def exportar_excel(df_pivot, df_persona, fechas_unicas, df_resultados, df_personal, dias_del_bloque, feriados_indices, fecha_inicio, offset_dia, file_name='Cronograma_Servicio_Kinesiologia.xlsx', crono_id=None):
    report = BaseReport(file_name, feriados=feriados_indices, fecha_inicio=fecha_inicio, crono_id=crono_id, servicio_id=1)
    
    # 1. Cronograma
    ws_c = report.generar_cronograma_sheet(df_pivot, fechas_unicas)
    if crono_id is not None:
        row_c = len(df_pivot) + 3
        ws_c.write(row_c, 0, "ID Cronograma:", report.styles.total_label)
        ws_c.write(row_c, 1, crono_id, report.styles.total_val)
    
    # 2. Vista por Personal
    ext_cols = ["Horas efectivas", "Horas lic", "Horas totales", "Seg M", "Seg T", "FS", "1/2 FS", "N"]
    ws_p, next_row = report.generar_vista_personal_sheet(df_persona, fechas_unicas, extension_columns=ext_cols, label_personal="KINESIÓLOGO")
    
    # Fila vacía de separación en Vista por Personal
    ws_p.write(next_row, 0, "", report.styles.cell)
    for col_idx, fecha in enumerate(fechas_unicas):
        is_sep = report._es_fin_de_semana_sep(fecha)
        fmt = report.styles.cell_week if is_sep else report.styles.cell
        ws_p.write(next_row, col_idx + 1, "", fmt)
    next_row += 1
    
    # Calcular y escribir filas de resumen
    totales_m, totales_t, totales_n = calcular_totales_por_turno(df_resultados, fechas_unicas)
    
    resumen_filas = [
        ("Total Mañana", totales_m),
        ("Total Tarde", totales_t),
        ("Total Noche", totales_n)
    ]
    
    for etiqueta, dic_totales in resumen_filas:
        ws_p.write(next_row, 0, etiqueta, report.styles.total_label)
        for col_idx, fecha in enumerate(fechas_unicas):
            val = dic_totales.get(fecha, 0)
            is_sep = report._es_fin_de_semana_sep(fecha)
            fmt = report.styles.total_val_week if is_sep else report.styles.total_val
            ws_p.write(next_row, col_idx + 1, val, fmt)
        next_row += 1
        
    if crono_id is not None:
        row_p = next_row + 1
        ws_p.write(row_p, 0, "ID Cronograma:", report.styles.total_label)
        ws_p.write(row_p, 1, crono_id, report.styles.total_val)
    
    # 3. Reporte de Horas (Standardized)
    from reportes.generales.base import calcular_resumen_estandar, asignar_horas_base
    df_reporte = calcular_resumen_estandar(df_resultados, df_personal, dias_del_bloque, feriados_indices, fecha_inicio, offset_dia, func_horas=asignar_horas_base)
    ws_r = report.generar_reporte_resumen_sheet(df_reporte, sheet_name='Reporte Histórico')
    if crono_id is not None:
        row_r = len(df_reporte) + 3
        ws_r.write(row_r, 0, "ID Cronograma:", report.styles.total_label)
        ws_r.write(row_r, 1, crono_id, report.styles.total_val)

    report.close()

def generar_y_exportar(df_resultados, df_personal, dias_del_bloque, feriados_indices, fecha_inicio, offset_dia, config_turnos, num_semanas, file_name=None, crono_id=None):
    if not file_name:
        from utils import obtener_nombre_archivo
        file_name = obtener_nombre_archivo('Cronograma_Servicio_Kinesiologia.xlsx', fecha_inicio)
        
    flrs_asignados = None
    if crono_id is not None:
        try:
            from database.connection import get_connection
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT nombre, fecha_inicio, fecha_fin
                    FROM flr_asignados
                    WHERE cronograma_id = ?
                """, (crono_id,))
                flrs_rows = cursor.fetchall()
                flrs_asignados = [{'nombre': r[0], 'fecha_inicio': r[1], 'fecha_fin': r[2]} for r in flrs_rows]
        except Exception as e:
            print(f"[reportes] Error al cargar FLRs asignados de la BD: {e}")
            
    df_pivot, fechas_unicas = exportar_excel_data_prep(df_resultados, config_turnos, df_personal=df_personal)
    df_persona = exportar_excel_vista_personal(df_resultados, df_personal, flrs_asignados=flrs_asignados)
    exportar_excel(df_pivot, df_persona, fechas_unicas, df_resultados, df_personal, dias_del_bloque, feriados_indices, fecha_inicio, offset_dia, file_name=file_name, crono_id=crono_id)

