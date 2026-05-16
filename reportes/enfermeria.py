import pandas as pd
from datetime import date, timedelta
import db as database
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

    for fecha in fechas_unicas:
        fecha_dt = date.fromisoformat(fecha)
        nombres_lpp = [n for n, r in database.LPP.items() if any(date.fromisoformat(i) <= fecha_dt <= date.fromisoformat(f) for i, f in r)]
        fila_lpp[fecha] = "\n".join(nombres_lpp)
        nombres_lar = [n for n, r in database.LAR.items() if any(date.fromisoformat(i) <= fecha_dt <= date.fromisoformat(f) for i, f in r)]
        fila_lar[fecha] = "\n".join(nombres_lar)

    filas_excel.append(fila_lpp)
    filas_excel.append(fila_lar)

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
                es_lar = any(date.fromisoformat(fi) <= fecha_dt <= date.fromisoformat(ff) for fi, ff in database.LAR.get(nombre, []))
                es_lpp = any(date.fromisoformat(fi) <= fecha_dt <= date.fromisoformat(ff) for i, f in database.LPP.get(nombre, [])) # Fix index error in logic if any
                # Re-check lpp/lar logic
                es_lar = any(date.fromisoformat(i) <= fecha_dt <= date.fromisoformat(f) for i, f in database.LAR.get(nombre, []))
                es_lpp = any(date.fromisoformat(i) <= fecha_dt <= date.fromisoformat(f) for i, f in database.LPP.get(nombre, []))

                if es_flr: fila[fecha] = "FLR"
                elif es_lar: fila[fecha] = "LAR"; dias_licencia += 1
                elif es_lpp: fila[fecha] = "LPP"; dias_licencia += 1
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

def exportar_excel(df_pivot, df_persona, fechas_unicas, df_resultados, df_personal, dias_del_bloque, feriados, fecha_inicio, offset_dia, file_name='Cronograma_Enfermeria_UTI.xlsx'):
    report = BaseReport(file_name)
    
    # 1. Cronograma
    report.generar_cronograma_sheet(df_pivot, fechas_unicas)
    
    # 2. Vista por Personal
    ext_cols = ["H. Efectivas", "H. Licencia", "H. Totales"]
    tipos_de_semana = ['M', 'T', 'TN', 'N']
    ext_cols += tipos_de_semana
    
    # Agregar conteo de semanas al df_persona antes de pasar al motor
    for t_label in tipos_de_semana:
        df_persona[t_label] = 0
        if df_cat_semanas is not None and not df_cat_semanas.empty:
            for nombre, row in df_persona.iterrows():
                conteo = len(df_cat_semanas[(df_cat_semanas['Nombre'] == nombre) & (df_cat_semanas['Categoria'] == t_label)])
                df_persona.at[nombre, t_label] = conteo

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

    # 3. Reporte de Horas (Standardized)
    from reportes.base import calcular_resumen_estandar, asignar_horas_base
    df_reporte = calcular_resumen_estandar(df_resultados, df_personal, dias_del_bloque, feriados, fecha_inicio, offset_dia, func_horas=asignar_horas_base)
    report.generar_reporte_resumen_sheet(df_reporte)
    
    report.close()

def generar_y_exportar(df_resultados, df_personal, dias_del_bloque, feriados, fecha_inicio, offset_dia, config_turnos, num_semanas, flrs_asignados=None, df_cat_semanas=None):
    df_pivot, fechas_unicas = exportar_excel_data_prep(df_resultados, config_turnos)
    df_persona = exportar_excel_vista_personal(df_resultados, df_personal, flrs_asignados)
    exportar_excel(df_pivot, df_persona, fechas_unicas, df_resultados, df_personal, dias_del_bloque, feriados, fecha_inicio, offset_dia)
