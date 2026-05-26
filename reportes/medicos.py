import pandas as pd
from datetime import date, timedelta
from database import queries as _db
from reportes.base import BaseReport

def asignar_horas_med(t):
    tipo = str(t).split('_')[0]
    if tipo == 'G': return 24
    if tipo in ['D', 'N']: return 12
    return 0

def get_abreviacion(turno):
    mapping = {
        "D_Planta": "D_P", "N_Planta": "N_P", "G_Planta": "G_P",
        "D_Residente": "D_R", "N_Residente": "N_R", "G_Residente": "G_R"
    }
    return mapping.get(turno, turno)

def exportar_excel_data_prep(df_resultados, df_personal):
    fechas_unicas = sorted(df_resultados['Fecha'].unique().tolist())
    turnos_unicos = sorted(df_resultados['Turno'].unique().tolist())
    
    filas_pivot = []
    # 1. Turnos normales
    for t_label in turnos_unicos:
        df_t = df_resultados[df_resultados['Turno'] == t_label]
        max_p = 0
        for f in fechas_unicas:
            c = len(df_t[df_t['Fecha'] == f])
            if c > max_p: max_p = c
            
        for i in range(max(1, max_p)):
            fila = {"Turno": t_label}
            for f in fechas_unicas:
                # Corregido: Usar 'Personal' en lugar de 'Kinesiologo' si existe
                col_nombre = 'Kinesiologo' if 'Kinesiologo' in df_t.columns else 'Personal'
                pers = df_t[df_t['Fecha'] == f].sort_values(by=col_nombre)[col_nombre].tolist()
                fila[f] = pers[i] if i < len(pers) else ""
            filas_pivot.append(fila)
            
    # 2. Filas de Licencias
    filas_pivot.append({"Turno": "  "}) # Espaciador
    for l_tipo in ["LPP", "LAR", "LM", "CM"]:
        fila_l = {"Turno": l_tipo}
        l_dict = getattr(_db, l_tipo, {})
        nombres_personal = set(df_personal['Nombre'].tolist())
        for f in fechas_unicas:
            nombres_l = []
            for nombre, rangos in l_dict.items():
                if nombre in nombres_personal and any(r[0] <= f <= r[1] for r in rangos):
                    nombres_l.append(nombre)
            fila_l[f] = "\n".join(nombres_l)
        filas_pivot.append(fila_l)

    df_pivot = pd.DataFrame(filas_pivot).set_index("Turno")
    return df_pivot, fechas_unicas

def exportar_excel_vista_personal(df_resultados, df_personal, flrs_asignados=None, dias_del_bloque=None):
    from data import FERIADOS
    fechas = sorted(df_resultados['Fecha'].unique().tolist())
    nombres = sorted(df_personal['Nombre'].tolist())
    col_nombre = 'Kinesiologo' if 'Kinesiologo' in df_resultados.columns else 'Personal'
    
    # Calcular bloques de descanso para segregar fines de semana comunes vs. largos (FSL3/FSL4)
    date_to_block_len = {}
    if fechas:
        fecha_inicio_dt = date.fromisoformat(fechas[0])
        fecha_fin_dt = date.fromisoformat(fechas[-1])
        total_dias = (fecha_fin_dt - fecha_inicio_dt).days + 1
        
        es_descanso = []
        for d in range(total_dias):
            f_str = (fecha_inicio_dt + timedelta(days=d)).isoformat()
            dt = fecha_inicio_dt + timedelta(days=d)
            es_f = dt.weekday() >= 5 or f_str in FERIADOS
            es_descanso.append(es_f)
            
        bloques = []; b_act = []
        for d in range(total_dias):
            if es_descanso[d]:
                b_act.append((fecha_inicio_dt + timedelta(days=d)).isoformat())
            else:
                if b_act:
                    bloques.append(b_act)
                    b_act = []
        if b_act:
            bloques.append(b_act)
            
        for b in bloques:
            for f_str in b:
                date_to_block_len[f_str] = len(b)

    def es_finde(f_str):
        dt = date.fromisoformat(f_str)
        return dt.weekday() >= 5 and date_to_block_len.get(f_str, 0) <= 2

    filas = []
    for nombre in nombres:
        fila = {"Personal": nombre}
        h_efectivas = 0
        h_licencia = 0
        fs_semanas_trabajadas = set()
        for fecha in fechas:
            asig = df_resultados[(df_resultados[col_nombre] == nombre) & (df_resultados['Fecha'] == fecha)]
            if not asig.empty:
                t = asig.iloc[0]['Turno']
                fila[fecha] = get_abreviacion(t) 
                h_efectivas += asignar_horas_med(t)
                if es_finde(fecha):
                    dt = date.fromisoformat(fecha)
                    lunes = (dt - timedelta(days=dt.weekday())).isoformat()
                    fs_semanas_trabajadas.add(lunes)
            else:
                # Buscar Licencias
                tipo_lic = ""
                for l_tipo in ["LAR", "LPP", "LM", "CM"]:
                    l_dict = getattr(_db, l_tipo, {})
                    if any(r[0] <= fecha <= r[1] for r in l_dict.get(nombre, [])):
                        tipo_lic = l_tipo
                        break
                
                if tipo_lic:
                    fila[fecha] = tipo_lic
                    h_licencia += (36.0 / 7.0) 
                else:
                    fila[fecha] = "F"
        fs_trabajados = len(fs_semanas_trabajadas)
        
        # 1. Calcular FS Disponibles (semanas sin licencia en todos los días del fin de semana)
        findes = {}
        if fechas:
            for f in fechas:
                dt = date.fromisoformat(f)
                es_f = dt.weekday() >= 5 or f in FERIADOS
                if es_f:
                    lunes = (dt - timedelta(days=dt.weekday())).isoformat()
                    findes.setdefault(lunes, []).append(f)
        
        lic_days = set()
        for f in fechas:
            for l_tipo in ["LAR", "LPP", "LM", "CM"]:
                l_dict = getattr(_db, l_tipo, {})
                if any(r[0] <= f <= r[1] for r in l_dict.get(nombre, [])):
                    lic_days.add(f)
                    break
        
        fs_disponibles = sum(1 for lunes, dias in findes.items() if any(d not in lic_days for d in dias))
        
        # 2. Calcular FSL3 y FSL4 Trabajados para FS Totales
        fsl3_trabajados = 0
        fsl4_trabajados = 0
        for b in bloques:
            worked_any = False
            for f in b:
                asig = df_resultados[(df_resultados[col_nombre] == nombre) & (df_resultados['Fecha'] == f)]
                if not asig.empty:
                    worked_any = True
                    break
            if worked_any:
                if len(b) == 3:
                    fsl3_trabajados += 1
                elif len(b) >= 4:
                    fsl4_trabajados += 1
                    
        fs_totales = fs_trabajados + fsl3_trabajados + fsl4_trabajados
        
        # 3. Calcular Viernes Trabajados
        viernes_trabajados = 0
        for f in fechas:
            dt = date.fromisoformat(f)
            if dt.weekday() == 4: # Friday
                asig = df_resultados[(df_resultados[col_nombre] == nombre) & (df_resultados['Fecha'] == f)]
                if not asig.empty:
                    viernes_trabajados += 1
        
        h_tot_calc = h_efectivas + h_licencia
        h_reg_mensual = df_personal[df_personal['Nombre'] == nombre]['horas_mensuales_reglamentarias'].iloc[0] or 144
        # Prorratear por días reales del bloque (si se conoce), default 30 días
        _dias_bloque = dias_del_bloque if dias_del_bloque and dias_del_bloque > 0 else 30
        h_obj = round(h_reg_mensual * _dias_bloque / 30.0, 1)
        extras = (h_tot_calc - h_obj) / 24.0
        
        fila["Horas Ef."] = int(h_efectivas)
        fila["Horas Lic."] = int(h_licencia + 0.5)
        fila["Horas Tot."] = int(h_tot_calc + 0.5)
        fila["Extras"] = round(extras, 1)
        fila["FS Disponibles"] = fs_disponibles
        fila["FS trabajados"] = fs_totales
        fila["Viernes trabajados"] = viernes_trabajados
        filas.append(fila)
        
    return pd.DataFrame(filas).set_index("Personal")

def calcular_resumen_medicos(df_resultados, df_personal, dias_del_bloque, feriados_indices, fecha_inicio, offset_dia):
    from database import queries as _db
    from datetime import date, timedelta
    from data import FERIADOS
    
    fecha_inicio_dt = pd.to_datetime(fecha_inicio)
    fecha_fin = (date.fromisoformat(fecha_inicio) + timedelta(days=dias_del_bloque - 1)).isoformat()
    ajustes_reglas = _db.cargar_ajustes_reglas_personal(fecha_inicio, fecha_fin)
    
    col_nombre = 'Kinesiologo' if 'Kinesiologo' in df_resultados.columns else 'Personal'
    
    # Calcular bloques de descanso para segregar fines de semana comunes vs. largos (FSL3/FSL4)
    date_to_block_len = {}
    bloques = []
    if dias_del_bloque > 0:
        es_descanso = []
        for d in range(dias_del_bloque):
            f_str = (date.fromisoformat(fecha_inicio) + timedelta(days=d)).isoformat()
            dt = date.fromisoformat(fecha_inicio) + timedelta(days=d)
            es_f = dt.weekday() >= 5 or f_str in FERIADOS
            es_descanso.append(es_f)
            
        b_act = []
        for d in range(dias_del_bloque):
            if es_descanso[d]:
                b_act.append((date.fromisoformat(fecha_inicio) + timedelta(days=d)).isoformat())
            else:
                if b_act:
                    bloques.append(b_act)
                    b_act = []
        if b_act:
            bloques.append(b_act)
            
        for b in bloques:
            for f_str in b:
                date_to_block_len[f_str] = len(b)

    def es_finde(f_str):
        dt = date.fromisoformat(f_str)
        return dt.weekday() >= 5 and date_to_block_len.get(f_str, 0) <= 2
        
    resumen = []
    for _, p in df_personal.iterrows():
        nombre = p['Nombre']
        
        # Calcular horas efectivas, licencia y fines de semana del período actual
        h_efectivas = 0
        h_licencia = 0
        fs_semanas_trabajadas = set()
        # Iterar sobre las fechas del período actual
        for d in range(dias_del_bloque):
            fecha_d = (date.fromisoformat(fecha_inicio) + timedelta(days=d)).isoformat()
            asig = df_resultados[(df_resultados[col_nombre] == nombre) & (df_resultados['Fecha'] == fecha_d)]
            if not asig.empty:
                t = asig.iloc[0]['Turno']
                h_efectivas += asignar_horas_med(t)
                if es_finde(fecha_d):
                    dt = date.fromisoformat(fecha_d)
                    lunes = (dt - timedelta(days=dt.weekday())).isoformat()
                    fs_semanas_trabajadas.add(lunes)
            else:
                # Buscar Licencias
                tipo_lic = ""
                for l_tipo in ["LAR", "LPP", "LM", "CM"]:
                    l_dict = getattr(_db, l_tipo, {})
                    if any(r[0] <= fecha_d <= r[1] for r in l_dict.get(nombre, [])):
                        tipo_lic = l_tipo
                        break
                
                if tipo_lic:
                    h_licencia += (36.0 / 7.0)
        fs_trabajados = len(fs_semanas_trabajadas)
                    
        # FSL3 y FSL4 del período actual
        fsl3_trabajados = 0
        fsl4_trabajados = 0
        for b in bloques:
            worked_any = False
            for f in b:
                asig = df_resultados[(df_resultados[col_nombre] == nombre) & (df_resultados['Fecha'] == f)]
                if not asig.empty:
                    worked_any = True
                    break
            if worked_any:
                if len(b) == 3:
                    fsl3_trabajados += 1
                elif len(b) >= 4:
                    fsl4_trabajados += 1
                    
        # a. Horas reglamentarias (prorrateadas por días reales del bloque)
        h_reg_mensual = p.get('horas_mensuales_reglamentarias', 144) or 144
        h_reg = round(h_reg_mensual * dias_del_bloque / 30.0, 1)
        
        # b. Límite de carga / Horas posibles totales para extra posibles
        max_horas = 192  # default
        for a in ajustes_reglas.get(nombre, []):
            if a['codigo_regla'] == 'MAX_HORAS_MES_CALENDARIO' and a['accion'] == 'SOBRESCRIBIR':
                if a['params'] and 'max_horas' in a['params']:
                    max_horas = a['params']['max_horas']
                    
        h_extra_posibles = (max_horas - h_reg) / 24.0
        
        # c. Horas totales del período actual (trabajadas + licencia)
        h_tot_calc = h_efectivas + h_licencia
        
        # d. Guardias extras realizadas en el período
        extras_realizadas = (h_tot_calc - h_reg) / 24.0
        
        # --- CUMULATIVE / HISTORICAL ---
        h_tot_acumulada = p.get('horas_anuales_previas', 0) + h_efectivas
        
        # Horas Posibles Histórico (pro-rata pro-meses pasados y bloque actual)
        f_ini_hist = p.get('fecha_inicio_historial')
        if f_ini_hist:
            dt_ini_hist = pd.to_datetime(f_ini_hist)
            meses_diff = (fecha_inicio_dt.year - dt_ini_hist.year) * 12 + (fecha_inicio_dt.month - dt_ini_hist.month)
            h_posibles_prev = max(0, meses_diff) * h_reg
        else:
            h_posibles_prev = 0
            
        # Licencias en el bloque actual
        dias_lic = 0
        for l_tipo in ["LAR", "LPP", "LM", "CM"]:
            l_dict = getattr(_db, l_tipo, {})
            for r in l_dict.get(nombre, []):
                l_ini = pd.to_datetime(r[0]); l_fin = pd.to_datetime(r[1])
                b_ini = fecha_inicio_dt; b_fin = fecha_inicio_dt + pd.Timedelta(days=dias_del_bloque-1)
                inter_ini = max(l_ini, b_ini); inter_fin = min(l_fin, b_fin)
                if inter_ini <= inter_fin:
                    dias_lic += (inter_fin - inter_ini).days + 1
                    
        # Pro-rata del bloque actual: (Horas / dias_del_bloque) * (dias_del_bloque - dias_lic)
        h_posibles_bloque = (h_reg_mensual / 30.0) * (dias_del_bloque - dias_lic)
        if h_posibles_bloque < 0: h_posibles_bloque = 0
        
        h_posibles_acumuladas = h_posibles_prev + h_posibles_bloque
        carga = (h_tot_acumulada / h_posibles_acumuladas * 100) if h_posibles_acumuladas > 0 else 0
        
        fs_acumulado = int(p.get('findes_semanas_previos', 0) + fs_trabajados)
        fsl3_acumulado = int(p.get('findes_largos_3_previos', 0) + fsl3_trabajados)
        fsl4_acumulado = int(p.get('findes_largos_4_previos', 0) + fsl4_trabajados)
        
        resumen.append({
            'Personal': nombre,
            # Período actual (nuevas columnas)
            'Horas reglamentarias': int(h_reg),
            'Guardias extra posibles': round(h_extra_posibles, 1),
            'Horas totales (trabajadas + licencia)': int(h_tot_calc + 0.5),
            'Guardias extras realizadas': round(extras_realizadas, 1),
            'FS trabajados': int(fs_trabajados),
            'FSL3 trabajados': int(fsl3_trabajados),
            'FSL4 trabajados': int(fsl4_trabajados),
            # Acumulado / Resumen (columnas estándar)
            'Horas Totales': int(h_tot_acumulada + 0.5),
            'Horas Posibles': int(h_posibles_acumuladas + 0.5),
            'Carga Horaria': f"{round(carga, 1)}%",
            'FS': fs_acumulado,
            'FSL3': fsl3_acumulado,
            'FSL4': fsl4_acumulado
        })
        
    return pd.DataFrame(resumen).sort_values(by='Carga Horaria', ascending=False)

def generar_reporte_horas(df_resultados):
    df_reporte_horas = df_resultados.copy()
    col_nombre = 'Kinesiologo' if 'Kinesiologo' in df_resultados.columns else 'Personal'
    
    def asignar_horas_med(t):
        tipo = str(t).split('_')[0]
        if tipo == 'G': return 24
        if tipo in ['D', 'N']: return 12
        return 0
        
    df_reporte_horas['Horas'] = df_reporte_horas['Turno'].apply(asignar_horas_med)
    horas_por_persona = df_reporte_horas.groupby(col_nombre)['Horas'].sum().reset_index()
    reporte_final = horas_por_persona.rename(columns={col_nombre: 'Personal', 'Horas': 'Horas Totales'})
    return reporte_final.sort_values(by='Horas Totales', ascending=False).reset_index(drop=True)

def exportar_excel(df_pivot, df_persona, fechas_unicas, df_resultados, df_personal, dias_del_bloque, feriados, fecha_inicio, offset_dia, file_name='Cronograma_Area_Medica_UTI.xlsx', crono_id=None):
    report = BaseReport(file_name, feriados=feriados, fecha_inicio=fecha_inicio, crono_id=crono_id)
    
    # 1. Cronograma
    ws_c = report.generar_cronograma_sheet(df_pivot, fechas_unicas)
    if crono_id is not None:
        row_c = len(df_pivot) + 3
        ws_c.write(row_c, 0, "ID Cronograma:", report.styles.total_label)
        ws_c.write(row_c, 1, crono_id, report.styles.total_val)
    
    # 2. Vista por Personal
    ext_cols = ["Horas Ef.", "Horas Lic.", "Horas Tot.", "Extras", "FS Disponibles", "FS trabajados", "Viernes trabajados"]
    ws_p, row_end = report.generar_vista_personal_sheet(df_persona, fechas_unicas, extension_columns=ext_cols, label_personal="MÉDICO")
    
    # --- TOTALES POR ROL (Específico de médicos) ---
    row_end += 1
    rol_map = df_personal.set_index('Nombre')['Rol'].to_dict()
    categorias = [
        ("Día Planta", "Planta", ["D", "G"]), 
        ("Día Resi", "Residente", ["D", "G"]), 
        ("Noche Planta", "Planta", ["N", "G"]), 
        ("Noche Resi", "Residente", ["N", "G"])
    ]
    
    for label, rol_buscado, turnos_match in categorias:
        ws_p.write(row_end, 0, label, report.styles.total_label)
        for col_idx, fecha in enumerate(fechas_unicas):
            count = 0
            for nombre, row_p in df_persona.iterrows():
                val = str(row_p[fecha])
                if rol_map.get(nombre) == rol_buscado:
                    if any(tm in val for tm in turnos_match):
                        count += 1
            is_sep = report._es_fin_de_semana_sep(fecha)
            ws_p.write(row_end, col_idx + 1, count, report.styles.total_val_week if is_sep else report.styles.total_val)
        row_end += 1

    # --- REFERENCIAS DE TURNOS Y ESTADOS ---
    row_end += 2
    ws_p.write(row_end, 0, "REFERENCIAS DE TURNOS Y ESTADOS:", report.styles.name_cell)
    row_end += 1
    
    referencias = [
        ("D_P", "Día Planta (Turno de Día - Médico de Planta)"),
        ("N_P", "Noche Planta (Turno de Noche - Médico de Planta)"),
        ("G_P", "Guardia Planta (Guardia de 24 hs - Médico de Planta)"),
        ("D_R", "Día Residente (Turno de Día - Residente)"),
        ("N_R", "Noche Residente (Turno de Noche - Residente)"),
        ("G_R", "Guardia Residente (Guardia de 24 hs - Residente)"),
        ("F", "Franco (Día Libre)"),
        ("LAR", "Licencia Anual Reglamentaria"),
        ("LPP", "Licencia por Paternidad / Particular"),
        ("LM", "Licencia Médica"),
        ("CM", "Carpeta Médica"),
    ]
    for sigla, desc in referencias:
        ws_p.write(row_end, 0, sigla, report.styles.header_light)
        ws_p.write(row_end, 1, desc, report.styles.cell)
        row_end += 1

    if crono_id is not None:
        row_end += 2
        ws_p.write(row_end, 0, "ID Cronograma:", report.styles.total_label)
        ws_p.write(row_end, 1, crono_id, report.styles.total_val)

    # 3. Reporte de Horas (Customizado para médicos)
    df_reporte = calcular_resumen_medicos(df_resultados, df_personal, dias_del_bloque, feriados, fecha_inicio, offset_dia)
    ws_r = report.generar_reporte_resumen_sheet(df_reporte)
    
    # --- REFERENCIAS / EXPLICACIONES DE LAS COLUMNAS ---
    row_ex = len(df_reporte) + 3
    ws_r.write(row_ex, 0, "REFERENCIA DE COLUMNAS DEL REPORTE:", report.styles.name_cell)
    row_ex += 1
    
    explicaciones = [
        ("Horas reglamentarias", "Horas mensuales obligatorias según régimen, prorrateadas por los días reales del bloque (ej: 144 hs × 30 días / 30 = 144; o 144 × 28 / 30 = 134.4)."),
        ("Guardias extra posibles", "Máximo de guardias extras de 24 hs permitidas en el período actual según el límite de carga horaria (ej: (192 - 144)/24 = 2)."),
        ("Horas totales (trabajadas + licencia)", "Suma de horas efectivamente trabajadas más horas teóricas por licencias (LAR, LPP, LM, CM) en el período actual."),
        ("Guardias extras realizadas", "Cantidad de guardias extras de 24 hs realmente realizadas en el período actual (ej: (Horas totales - Horas reglamentarias) / 24)."),
        ("FS trabajados", "Cantidad de fines de semana comunes (de hasta 2 días) trabajados en el período actual."),
        ("FSL3 trabajados", "Cantidad de fines de semana largos de 3 días trabajados en el período actual."),
        ("FSL4 trabajados", "Cantidad de fines de semana largos de 4 días o más trabajados en el período actual."),
        ("Horas Totales", "Historial acumulado de horas totales (histórico acumulado + horas efectivas del período actual)."),
        ("Horas Posibles", "Historial acumulado de horas reglamentarias teóricas correspondientes a los meses del historial."),
        ("Carga Horaria", "Relación porcentual de cumplimiento de horas (Horas Totales / Horas Posibles * 100)."),
        ("FS", "Historial acumulado total de fines de semana comunes trabajados."),
        ("FSL3", "Historial acumulado total de fines de semana largos de 3 días trabajados."),
        ("FSL4", "Historial acumulado total de fines de semana largos de 4 días o más trabajados."),
    ]
    
    for col_name, desc in explicaciones:
        ws_r.write(row_ex, 0, col_name, report.styles.header_light)
        ws_r.write(row_ex, 1, desc, report.styles.cell)
        row_ex += 1

    if crono_id is not None:
        row_ex += 2
        ws_r.write(row_ex, 0, "ID Cronograma:", report.styles.total_label)
        ws_r.write(row_ex, 1, crono_id, report.styles.total_val)
    
    report.close()

def generar_y_exportar(df_resultados, df_personal, dias_del_bloque, feriados, fecha_inicio, offset_dia, config_turnos, num_semanas, flrs_asignados=None, df_cat_semanas=None, crono_id=None):
    df_pivot, fechas_unicas = exportar_excel_data_prep(df_resultados, df_personal)
    df_persona = exportar_excel_vista_personal(df_resultados, df_personal, flrs_asignados, dias_del_bloque=dias_del_bloque)
    exportar_excel(df_pivot, df_persona, fechas_unicas, df_resultados, df_personal, dias_del_bloque, feriados, fecha_inicio, offset_dia, crono_id=crono_id)

