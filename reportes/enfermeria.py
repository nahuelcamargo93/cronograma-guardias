import pandas as pd
from datetime import date
import db as database

def exportar_excel_data_prep(df_resultados, config_turnos):
    # --- PIVOTEAR EL CRONOGRAMA ---
    df_excel = df_resultados.copy()
    
    # Desdoblar turnos combinados (MT y TNN) solo para la vista
    filas_extra = []
    indices_a_borrar = []
    for idx, row in df_excel.iterrows():
        if row['Turno'] == 'MT':
            row_m = row.copy()
            row_m['Turno'] = "M"
            filas_extra.append(row_m)
            row_t = row.copy()
            row_t['Turno'] = "T"
            filas_extra.append(row_t)
            indices_a_borrar.append(idx)
        elif row['Turno'] == 'TNN':
            row_tn = row.copy()
            row_tn['Turno'] = "TN"
            filas_extra.append(row_tn)
            
            # La parte N de un TNN ocurre al día siguiente
            row_n = row.copy()
            row_n['Turno'] = "N"
            try:
                curr_date = date.fromisoformat(row_n['Fecha'])
                from datetime import timedelta
                row_n['Fecha'] = (curr_date + timedelta(days=1)).isoformat()
                filas_extra.append(row_n)
            except:
                filas_extra.append(row_n) # Fallback al mismo día si falla la fecha
            
    df_excel = df_excel.drop(indices_a_borrar)
    if filas_extra:
        df_excel = pd.concat([df_excel, pd.DataFrame(filas_extra)], ignore_index=True)
        
    fechas_unicas = sorted(df_excel['Fecha'].unique())
    # Orden cronológico: Noche (00-06) primero, Tarde-Noche (18-00) último
    turnos_ordenados = ["N", "M", "T", "TN"]
                
    filas_excel = []
    
    # Obtener jerarquía (por ahora todos son Rotativos o similar)
    rows_p = database.get_connection().execute("SELECT nombre, rol FROM personal WHERE servicio_id = 2").fetchall()
    jerarquia = {n: 1 for n, r in rows_p} # Todos igual por ahora

    for turno_label in turnos_ordenados:
        df_turno = df_excel[df_excel['Turno'] == turno_label]
        
        # Max personas asignadas en este turno en cualquier día
        max_personas_turno = 0
        for fecha in fechas_unicas:
            count = len(df_turno[df_turno['Fecha'] == fecha])
            if count > max_personas_turno:
                max_personas_turno = count
        
        if max_personas_turno == 0:
            # Aun si está vacío, el usuario pidió estas filas
            max_personas_turno = 1

        for i in range(max_personas_turno):
            fila = {"Turno": turno_label}
            for fecha in fechas_unicas:
                pers_dia = df_turno[df_turno['Fecha'] == fecha].sort_values(
                    by='Kinesiologo' # Se llama Kinesiologo en df_resultados por ahora (main.py)
                )['Kinesiologo'].tolist()
                fila[fecha] = pers_dia[i] if i < len(pers_dia) else ""
            filas_excel.append(fila)

    # --- AGREGAR FILAS DE LICENCIAS (LAR / LPP) ---
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
    # Obtener todas las fechas y nombres
    fechas = sorted(df_resultados['Fecha'].unique())
    nombres = sorted(df_personal['Nombre'].tolist())
    
    # Crear un mapa rápido de FLRs por persona
    mapa_flrs = {}
    if flrs_asignados:
        for flr in flrs_asignados:
            n = flr['nombre']
            fi = date.fromisoformat(flr['fecha_inicio'])
            ff = date.fromisoformat(flr['fecha_fin'])
            mapa_flrs.setdefault(n, []).append((fi, ff))

    siglas_dias = ["L", "M", "Mi", "J", "V", "S", "D"]
    
    def format_fecha(f_str):
        dt = date.fromisoformat(f_str)
        return f"{siglas_dias[dt.weekday()]} {dt.day}/{dt.month}"

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
            # 1. Buscar turno asignado
            asig = df_resultados[(df_resultados['Kinesiologo'] == nombre) & (df_resultados['Fecha'] == fecha)]
            if not asig.empty:
                t = asig.iloc[0]['Turno']
                fila[fecha] = t
                total_horas_efectivas += asignar_horas_enf(t)
            else:
                # 2. Buscar si es FLR actual
                es_flr = any(fi <= fecha_dt <= ff for fi, ff in mapa_flrs.get(nombre, []))
                # 3. Buscar si tiene licencia en esa fecha
                es_lar = any(date.fromisoformat(fi) <= fecha_dt <= date.fromisoformat(ff) for fi, ff in database.LAR.get(nombre, []))
                es_lpp = any(date.fromisoformat(fi) <= fecha_dt <= date.fromisoformat(ff) for fi, ff in database.LPP.get(nombre, []))
                
                if es_flr:
                    fila[fecha] = "FLR"
                elif es_lar: 
                    fila[fecha] = "LAR"
                    dias_licencia += 1
                elif es_lpp: 
                    fila[fecha] = "LPP"
                    dias_licencia += 1
                else: 
                    fila[fecha] = "F"
                    total_f += 1
        
        # Cálculo de horas de licencia (regla de 3 simple sobre 144hs)
        dias_periodo = len(fechas)
        horas_licencia = round((144.0 / dias_periodo) * dias_licencia, 1) if dias_periodo > 0 else 0
        
        fila["Horas Efectivas"] = total_horas_efectivas
        fila["Horas Licencia"] = horas_licencia
        fila["Horas Totales"] = total_horas_efectivas + horas_licencia
        fila["F"] = total_f
        filas.append(fila)
        
    return pd.DataFrame(filas).set_index("Enfermero")

def generar_reporte(df_resultados, df_personal, dias_del_bloque, feriados, fecha_inicio, offset_dia, num_semanas):
    # Reporte de control de horas
    df_reporte_horas = df_resultados.copy()
    # Horas: M, T, TN, N = 6hs | MT, TNN = 12hs
    def asignar_horas_enf(t):
        return 12 if t in ["MT", "TNN"] else 6
        
    df_reporte_horas['Horas'] = df_reporte_horas['Turno'].apply(asignar_horas_enf)
    horas_por_persona = df_reporte_horas.groupby('Kinesiologo')['Horas'].sum().reset_index()
    
    # ... (simplificado para enfermería por ahora, centrado en horas) ...
    reporte_final = horas_por_persona.rename(columns={'Kinesiologo': 'Enfermero', 'Horas': 'Horas Mensuales'})
    reporte_final = reporte_final.sort_values(by='Horas Mensuales', ascending=False).reset_index(drop=True)
    
    print("\nREPORTE DE CONTROL: HORAS ENFERMERIA")
    print(reporte_final.to_string())
    return reporte_final

def exportar_excel(df_pivot, df_persona, df_reporte, fechas_unicas, file_name='Cronograma_Enfermeria_UTI.xlsx'):
    with pd.ExcelWriter(file_name, engine='xlsxwriter') as writer:
        # --- HOJA 1: CRONOGRAMA POR TURNOS ---
        df_pivot.to_excel(writer, sheet_name='Cronograma')
        workbook  = writer.book
        worksheet = writer.sheets['Cronograma']

        header_fmt = workbook.add_format({'bold': True, 'bg_color': '#D7E4BD', 'border': 1, 'align': 'center'})
        cell_fmt = workbook.add_format({'text_wrap': True, 'valign': 'top', 'border': 1, 'font_size': 9})
        
        colores = {
            "M": '#EBF1DE', # Verde claro
            "T": '#FEF2CB', # Amarillo claro
            "TN": '#DAEEF3', # Azul claro
            "N": '#E5E0EC'  # Purpura claro
        }

        worksheet.set_column(0, 0, 15, header_fmt)
        worksheet.set_column(1, len(fechas_unicas), 15, cell_fmt)

        for i, (turno_label, row) in enumerate(df_pivot.iterrows()):
            fila_excel = i + 1
            if turno_label in ["LPP", "LAR"]:
                fmt = workbook.add_format({'bg_color': '#F2F2F2', 'italic': True, 'text_wrap': True, 'border': 1, 'valign': 'top', 'font_size': 8})
                altura = 30
            elif turno_label.strip() == "":
                fmt = workbook.add_format({'bg_color': '#FFFFFF', 'border': 0})
                altura = 15
            else:
                color = colores.get(turno_label, '#FFFFFF')
                fmt = workbook.add_format({'bg_color': color, 'text_wrap': True, 'border': 1, 'valign': 'top', 'font_size': 9})
                altura = 20
            
            worksheet.set_row(fila_excel, altura, fmt)

        # --- HOJA 2: VISTA POR PERSONAL (CUSTOMIZADA) ---
        ws_p = workbook.add_worksheet('Vista por Personal')
        
        # Formatos
        fmt_header_blue = workbook.add_format({'bold': True, 'bg_color': '#BDD7EE', 'border': 1, 'align': 'center', 'valign': 'vcenter'})
        fmt_header_light = workbook.add_format({'bold': True, 'bg_color': '#DDEBF7', 'border': 1, 'align': 'center', 'valign': 'vcenter', 'font_size': 9})
        fmt_name = workbook.add_format({'bold': True, 'bg_color': '#FCE4D6', 'border': 1, 'valign': 'vcenter'})
        fmt_cell = workbook.add_format({'border': 1, 'align': 'center', 'valign': 'vcenter', 'font_size': 9})
        fmt_sunday = workbook.add_format({'border': 1, 'right': 5, 'align': 'center', 'valign': 'vcenter', 'font_size': 9}) # right: 5 es grueso
        fmt_total_label = workbook.add_format({'bold': True, 'bg_color': '#E2EFDA', 'border': 1, 'align': 'right'})
        fmt_total_val = workbook.add_format({'bold': True, 'bg_color': '#E2EFDA', 'border': 1, 'align': 'center'})

        # Escribir Cabeceras (2 filas)
        ws_p.write(0, 0, "APELLIDO Y NOMBRE", fmt_header_blue)
        ws_p.write(1, 0, "", fmt_header_blue)
        ws_p.set_column(0, 0, 25)
        
        siglas_dias = ["L", "M", "Mi", "J", "V", "S", "D"]
        for col_idx, fecha in enumerate(fechas_unicas):
            dt = date.fromisoformat(fecha)
            sigla = siglas_dias[dt.weekday()]
            dia_num = f"{dt.day}/{dt.month}"
            
            style = fmt_header_blue if dt.weekday() != 6 else workbook.add_format({'bold': True, 'bg_color': '#BDD7EE', 'border': 1, 'right': 5, 'align': 'center'})
            ws_p.write(0, col_idx + 1, sigla, style)
            
            style_l = fmt_header_light if dt.weekday() != 6 else workbook.add_format({'bold': True, 'bg_color': '#DDEBF7', 'border': 1, 'right': 5, 'align': 'center', 'font_size': 9})
            ws_p.write(1, col_idx + 1, dia_num, style_l)
            ws_p.set_column(col_idx + 1, col_idx + 1, 5)

        # Totales de Horas al final
        col_offset = len(fechas_unicas) + 1
        ws_p.merge_range(0, col_offset, 1, col_offset, "H. Efectivas", fmt_header_blue)
        ws_p.merge_range(0, col_offset + 1, 1, col_offset + 1, "H. Licencia", fmt_header_blue)
        ws_p.merge_range(0, col_offset + 2, 1, col_offset + 2, "H. Totales", fmt_header_blue)
        ws_p.merge_range(0, col_offset + 3, 1, col_offset + 3, "Francos", fmt_header_blue)
        ws_p.set_column(col_offset, col_offset + 3, 10)

        # Escribir Datos de Personal
        fila_excel = 2
        for nombre, row in df_persona.iterrows():
            ws_p.write(fila_excel, 0, nombre, fmt_name)
            for col_idx, fecha in enumerate(fechas_unicas):
                val = row[fecha]
                dt = date.fromisoformat(fecha)
                
                # Formato base
                fmt = fmt_cell
                if dt.weekday() == 6: fmt = fmt_sunday
                
                # Colores por tipo
                if val in ["F", "LAR", "LPP"]:
                    fmt = workbook.add_format({'bg_color': '#D9D9D9', 'font_color': '#595959', 'border': 1, 'align': 'center'})
                    if dt.weekday() == 6: fmt.set_right(5)
                elif val == "FLR":
                    fmt = workbook.add_format({'bg_color': '#A6A6A6', 'font_color': '#FFFFFF', 'bold': True, 'border': 1, 'align': 'center'})
                    if dt.weekday() == 6: fmt.set_right(5)
                
                ws_p.write(fila_excel, col_idx + 1, val, fmt)
            
            # Horas
            ws_p.write(fila_excel, col_offset, row["Horas Efectivas"], fmt_cell)
            ws_p.write(fila_excel, col_offset + 1, row["Horas Licencia"], fmt_cell)
            ws_p.write(fila_excel, col_offset + 2, row["Horas Totales"], fmt_cell)
            ws_p.write(fila_excel, col_offset + 3, row["F"], fmt_cell)
            fila_excel += 1

        # --- FILA VACÍA Y TOTALES POR FRANJA ---
        fila_excel += 1 # Una fila vacía
        
        # Necesitamos el df desdoblado para contar bien
        from datetime import timedelta
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
            else:
                filas_extra.append(r)
        df_desdoblado = pd.DataFrame(filas_extra)

        for turno_count in ["M", "T", "TN", "N"]:
            ws_p.write(fila_excel, 0, f"TOTAL {turno_count}", fmt_total_label)
            for col_idx, fecha in enumerate(fechas_unicas):
                dt = date.fromisoformat(fecha)
                count = len(df_desdoblado[(df_desdoblado['Fecha'] == fecha) & (df_desdoblado['Turno'] == turno_count)])
                
                fmt = fmt_total_val
                if dt.weekday() == 6:
                    fmt = workbook.add_format({'bold': True, 'bg_color': '#E2EFDA', 'border': 1, 'right': 5, 'align': 'center'})
                
                ws_p.write(fila_excel, col_idx + 1, count if count > 0 else 0, fmt)
            fila_excel += 1

        df_reporte.to_excel(writer, sheet_name='Reporte de Horas', index=False)

    print("¡Excel generado con éxito! Archivo:", file_name)

def generar_y_exportar(df_resultados, df_personal, dias_del_bloque, feriados_indices, fecha_inicio, offset_dia, config_turnos, num_semanas, flrs_asignados=None):
    df_pivot, fechas_unicas = exportar_excel_data_prep(df_resultados, config_turnos)
    df_persona = exportar_excel_vista_personal(df_resultados, df_personal, flrs_asignados)
    df_reporte = generar_reporte(df_resultados, df_personal, dias_del_bloque, feriados_indices, fecha_inicio, offset_dia, num_semanas)
    exportar_excel(df_pivot, df_persona, df_reporte, fechas_unicas)
