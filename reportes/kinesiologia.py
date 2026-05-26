import pandas as pd
from datetime import date, timedelta
from database import queries as database
from reportes.base import BaseReport

def exportar_excel_data_prep(df_resultados, config_turnos):
    # --- PIVOTEAR EL CRONOGRAMA ---
    df_excel = df_resultados.copy()
    
    # Desdoblar turnos "Dia_" solo para la vista
    filas_extra = []
    indices_a_borrar = []
    for idx, row in df_excel.iterrows():
        if row['Turno'].startswith('Dia_'):
            suffix = row['Turno'].replace('Dia_', '')
            row_m = row.copy(); row_m['Turno'] = f"Mañana_{suffix}"; filas_extra.append(row_m)
            row_t = row.copy(); row_t['Turno'] = f"Tarde_{suffix}"; filas_extra.append(row_t)
            indices_a_borrar.append(idx)
            
    df_excel = df_excel.drop(indices_a_borrar)
    if filas_extra:
        df_excel = pd.concat([df_excel, pd.DataFrame(filas_extra)], ignore_index=True)
        
    fechas_unicas = sorted(df_excel['Fecha'].unique().tolist())
    turnos_ordenados = []
    for tipo in ["Semana", "Finde_Feriado"]:
        for t in config_turnos.get(tipo, {}).keys():
            if t not in turnos_ordenados:
                turnos_ordenados.append(t)
                
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
                fila[f] = pers_dia[i] if i < len(pers_dia) else ""
            filas_excel.append(fila)

    # Licencias
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

def exportar_excel_vista_personal(df_resultados, df_personal):
    fechas = sorted(df_resultados['Fecha'].unique())
    nombres = sorted(df_personal['Nombre'].tolist())
    
    col_nombre = 'Personal' if 'Personal' in df_resultados.columns else 'Kinesiologo'
    
    filas = []
    for nombre in nombres:
        fila = {col_nombre: nombre}
        for fecha in fechas:
            asig = df_resultados[(df_resultados[col_nombre] == nombre) & (df_resultados['Fecha'] == fecha)]
            if not asig.empty:
                fila[fecha] = asig.iloc[0]['Turno']
            else:
                fecha_dt = date.fromisoformat(fecha)
                es_lar = any(date.fromisoformat(i) <= fecha_dt <= date.fromisoformat(f) for i, f in database.LAR.get(nombre, []))
                es_lpp = any(date.fromisoformat(i) <= fecha_dt <= date.fromisoformat(f) for i, f in database.LPP.get(nombre, []))
                es_lm = any(date.fromisoformat(i) <= fecha_dt <= date.fromisoformat(f) for i, f in getattr(database, 'LM', {}).get(nombre, []))
                es_cm = any(date.fromisoformat(i) <= fecha_dt <= date.fromisoformat(f) for i, f in getattr(database, 'CM', {}).get(nombre, []))
                if es_lar: fila[fecha] = "LAR"
                elif es_lpp: fila[fecha] = "LPP"
                elif es_lm: fila[fecha] = "LM"
                elif es_cm: fila[fecha] = "CM"
                else: fila[fecha] = "F"
        filas.append(fila)
    return pd.DataFrame(filas).set_index(col_nombre)

from reportes.base import asignar_horas_base

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

def exportar_excel(df_pivot, df_persona, fechas_unicas, df_resultados, df_personal, dias_del_bloque, feriados_indices, fecha_inicio, offset_dia, file_name='Cronograma_Servicio_Kinesiologia.xlsx', crono_id=None):
    report = BaseReport(file_name, feriados=feriados_indices, fecha_inicio=fecha_inicio, crono_id=crono_id)
    
    # 1. Cronograma
    ws_c = report.generar_cronograma_sheet(df_pivot, fechas_unicas)
    if crono_id is not None:
        row_c = len(df_pivot) + 3
        ws_c.write(row_c, 0, "ID Cronograma:", report.styles.total_label)
        ws_c.write(row_c, 1, crono_id, report.styles.total_val)
    
    # 2. Vista por Personal
    ws_p, _ = report.generar_vista_personal_sheet(df_persona, fechas_unicas, label_personal="KINESIÓLOGO")
    if crono_id is not None:
        row_p = len(df_persona) + 3
        ws_p.write(row_p, 0, "ID Cronograma:", report.styles.total_label)
        ws_p.write(row_p, 1, crono_id, report.styles.total_val)
    
    # 3. Reporte de Horas (Standardized)
    from reportes.base import calcular_resumen_estandar, asignar_horas_base
    df_reporte = calcular_resumen_estandar(df_resultados, df_personal, dias_del_bloque, feriados_indices, fecha_inicio, offset_dia, func_horas=asignar_horas_base)
    ws_r = report.generar_reporte_resumen_sheet(df_reporte)
    if crono_id is not None:
        row_r = len(df_reporte) + 3
        ws_r.write(row_r, 0, "ID Cronograma:", report.styles.total_label)
        ws_r.write(row_r, 1, crono_id, report.styles.total_val)

    report.close()

def generar_y_exportar(df_resultados, df_personal, dias_del_bloque, feriados_indices, fecha_inicio, offset_dia, config_turnos, num_semanas, crono_id=None):
    df_pivot, fechas_unicas = exportar_excel_data_prep(df_resultados, config_turnos)
    df_persona = exportar_excel_vista_personal(df_resultados, df_personal)
    exportar_excel(df_pivot, df_persona, fechas_unicas, df_resultados, df_personal, dias_del_bloque, feriados_indices, fecha_inicio, offset_dia, crono_id=crono_id)
