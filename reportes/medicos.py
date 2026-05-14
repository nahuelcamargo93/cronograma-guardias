import pandas as pd
from datetime import date, timedelta
import database.queries as database
import rule_engine as _re
from data import SERVICIO_ID, FECHA_INICIO

def exportar_excel_data_prep(df_resultados, df_personal):
    # --- PIVOTEAR EL CRONOGRAMA ---
    df_excel = df_resultados.copy()
    
    # Mapear el nombre del turno a una etiqueta descriptiva (ej: G_Planta -> G Planta)
    df_excel['Turno_Slot'] = df_excel['Turno'].apply(lambda x: x.replace('_', ' '))
        
    fechas_unicas = sorted(df_resultados['Fecha'].unique())
    # Ordenar etiquetas: Planta primero, luego Residentes. G, luego D, luego N.
    orden_base = ["D Planta", "D Residente", "G Planta", "G Residente", "N Planta", "N Residente"]
    
    # Solo incluir etiquetas que realmente existan en los resultados
    turnos_existentes = df_excel['Turno_Slot'].unique()
    turnos_ordenados = [t for t in orden_base if t in turnos_existentes]
    # Añadir cualquier otro que no esté en la lista base
    for t in turnos_existentes:
        if t not in turnos_ordenados:
            turnos_ordenados.append(t)
                
    filas_excel = []
    col_persona = 'Kinesiologo' if 'Kinesiologo' in df_resultados.columns else 'Personal'

    for turno_label in turnos_ordenados:
        df_turno = df_excel[df_excel['Turno_Slot'] == turno_label]
        
        max_personas_turno = 0
        for fecha in fechas_unicas:
            count = len(df_turno[df_turno['Fecha'] == fecha])
            if count > max_personas_turno:
                max_personas_turno = count
        
        filas_a_generar = max(1, max_personas_turno)

        for i in range(filas_a_generar):
            fila = {"Bloque": turno_label}
            for fecha in fechas_unicas:
                pers_dia = df_turno[df_turno['Fecha'] == fecha].sort_values(
                    by=col_persona
                )[col_persona].tolist()
                fila[fecha] = pers_dia[i] if i < len(pers_dia) else ""
            filas_excel.append(fila)

    # --- LICENCIAS (Filtradas por personal del servicio) ---
    nombres_servicio = set(df_personal['Nombre'].tolist())
    
    filas_excel.append({"Bloque": "  "}) 
    fila_lpp = {"Bloque": "LPP"}
    fila_lar = {"Bloque": "LAR"}
    fila_lm  = {"Bloque": "LM"}

    for fecha in fechas_unicas:
        fecha_dt = date.fromisoformat(fecha)
        # Solo traer si el nombre está en el servicio actual
        nombres_lpp = [n for n, r in database.LPP.items() if n in nombres_servicio and any(date.fromisoformat(i) <= fecha_dt <= date.fromisoformat(f) for i, f in r)]
        fila_lpp[fecha] = "\n".join(nombres_lpp)
        nombres_lar = [n for n, r in database.LAR.items() if n in nombres_servicio and any(date.fromisoformat(i) <= fecha_dt <= date.fromisoformat(f) for i, f in r)]
        fila_lar[fecha] = "\n".join(nombres_lar)
        nombres_lm = [n for n, r in database.LM.items() if n in nombres_servicio and any(date.fromisoformat(i) <= fecha_dt <= date.fromisoformat(f) for i, f in r)]
        fila_lm[fecha] = "\n".join(nombres_lm)

    filas_excel.append(fila_lpp)
    filas_excel.append(fila_lar)
    filas_excel.append(fila_lm)

    df_pivot = pd.DataFrame(filas_excel).set_index("Bloque")
    return df_pivot, fechas_unicas

def exportar_excel_vista_personal(df_resultados, df_personal, flrs_asignados=None):
    fechas = sorted(df_resultados['Fecha'].unique())
    nombres = sorted(df_personal['Nombre'].tolist())
    
    col_persona = 'Kinesiologo' if 'Kinesiologo' in df_resultados.columns else 'Personal'

    def asignar_horas_med(t):
        tipo = t.split('_')[0]
        if tipo == 'G': return 24
        if tipo in ['D', 'N']: return 12
        return 0

    # Cargar reglas para el cálculo de horas de licencia
    reglas_servicio = database.cargar_reglas_servicio(SERVICIO_ID)
    reglas_personal_all = database.cargar_reglas_personal(SERVICIO_ID)
    ajustes_personal_all = database.cargar_ajustes_reglas_personal(fechas[0], fechas[-1])

    filas = []
    for nombre in nombres:
        fila = {"Personal": nombre}
        total_horas_efectivas = 0
        total_f = 0
        dias_licencia = 0
        
        reglas_p = reglas_personal_all.get(nombre, {})

        for fecha in fechas:
            fecha_dt = date.fromisoformat(fecha)
            asig = df_resultados[(df_resultados[col_persona] == nombre) & (df_resultados['Fecha'] == fecha)]
            if not asig.empty:
                t = asig.iloc[0]['Turno']
                # Mostrar solo el nombre base del turno
                fila[fecha] = t.split('_')[0]
                total_horas_efectivas += asignar_horas_med(t)
            else:
                es_lar = any(date.fromisoformat(fi) <= fecha_dt <= date.fromisoformat(ff) for fi, ff in database.LAR.get(nombre, []))
                es_lpp = any(date.fromisoformat(fi) <= fecha_dt <= date.fromisoformat(ff) for fi, ff in database.LPP.get(nombre, []))
                es_lm  = any(date.fromisoformat(fi) <= fecha_dt <= date.fromisoformat(ff) for fi, ff in database.LM.get(nombre, []))
                
                if es_lar: 
                    fila[fecha] = "LAR"
                    dias_licencia += 1
                elif es_lpp: 
                    fila[fecha] = "LPP"
                    dias_licencia += 1
                elif es_lm:
                    fila[fecha] = "LM"
                    dias_licencia += 1
                else: 
                    fila[fecha] = "F"
                    total_f += 1
        
        # --- NUEVA LÓGICA DE CRÉDITO POR LICENCIA ---
        # Consultar la regla para la fecha de inicio del bloque
        p_cred = _re.resolver_parametros_regla('CREDITO_HORARIO_LICENCIA', nombre, FECHA_INICIO, reglas_servicio, reglas_p, ajustes_personal_all)
        
        if _re.regla_existe(p_cred):
            h_sem = p_cred.get('horas_por_semana', 36)
            horas_licencia = round((h_sem / 7.0) * dias_licencia, 1)
        else:
            # Fallback (Enfermería o si no está configurada)
            dias_periodo = len(fechas)
            horas_licencia = round((144.0 / dias_periodo) * dias_licencia, 1) if dias_periodo > 0 else 0
        
        fila["Horas Efectivas"] = total_horas_efectivas
        fila["Horas Licencia"] = horas_licencia
        fila["Horas Totales"] = total_horas_efectivas + horas_licencia
        fila["F"] = total_f
        filas.append(fila)
        
    return pd.DataFrame(filas).set_index("Personal")

def generar_reporte(df_resultados, df_personal):
    df_reporte_horas = df_resultados.copy()
    col_persona = 'Kinesiologo' if 'Kinesiologo' in df_resultados.columns else 'Personal'
    
    def asignar_horas_med(t):
        tipo = t.split('_')[0]
        if tipo == 'G': return 24
        if tipo in ['D', 'N']: return 12
        return 0
        
    df_reporte_horas['Horas'] = df_reporte_horas['Turno'].apply(asignar_horas_med)
    horas_por_persona = df_reporte_horas.groupby(col_persona)['Horas'].sum().reset_index()
    
    reporte_final = horas_por_persona.rename(columns={col_persona: 'Personal', 'Horas': 'Horas Totales'})
    reporte_final = reporte_final.sort_values(by='Horas Totales', ascending=False).reset_index(drop=True)
    
    print("\nREPORTE DE CONTROL: HORAS AREA MEDICA")
    print(reporte_final.to_string())
    return reporte_final

def exportar_excel(df_pivot, df_persona, df_reporte, fechas_unicas, df_resultados, df_personal, file_name='Cronograma_Area_Medica_UTI.xlsx'):
    with pd.ExcelWriter(file_name, engine='xlsxwriter') as writer:
        df_pivot.to_excel(writer, sheet_name='Cronograma')
        workbook  = writer.book
        worksheet = writer.sheets['Cronograma']

        header_fmt = workbook.add_format({'bold': True, 'bg_color': '#D7E4BD', 'border': 1, 'align': 'center'})
        cell_fmt = workbook.add_format({'text_wrap': True, 'valign': 'top', 'border': 1, 'font_size': 9})
        
        colores = {
            "G": '#F2F2F2', # Guardia
            "D": '#EBF1DE', # Día
            "N": '#DAEEF3'  # Noche
        }

        worksheet.set_column(0, 0, 15, header_fmt)
        worksheet.set_column(1, len(fechas_unicas), 15, cell_fmt)

        for i, (bloque, row) in enumerate(df_pivot.iterrows()):
            fila_excel = i + 1
            if bloque in ["LPP", "LAR", "LM"]:
                fmt = workbook.add_format({'bg_color': '#F2F2F2', 'italic': True, 'text_wrap': True, 'border': 1, 'valign': 'top', 'font_size': 8})
                altura = 30
            elif bloque.strip() == "":
                fmt = workbook.add_format({'bg_color': '#FFFFFF', 'border': 0})
                altura = 15
            else:
                color = '#FFFFFF'
                for k, c in colores.items():
                    if k in bloque:
                        color = c
                        break
                fmt = workbook.add_format({'bg_color': color, 'text_wrap': True, 'border': 1, 'valign': 'top', 'font_size': 9})
                altura = 25
            
            worksheet.set_row(fila_excel, altura, fmt)

        # --- VISTA POR PERSONAL ---
        df_persona.to_excel(writer, sheet_name='Vista por Personal')
        ws_p = writer.sheets['Vista por Personal']
        
        fmt_name = workbook.add_format({'bold': True, 'bg_color': '#FCE4D6', 'border': 1})
        ws_p.set_column(0, 0, 25, fmt_name)
        ws_p.set_column(1, len(fechas_unicas), 6, cell_fmt)
        ws_p.set_column(len(fechas_unicas) + 1, len(fechas_unicas) + 4, 12, header_fmt)

        # --- FILA VACÍA Y TOTALES POR FRANJA (Similar a enfermería) ---
        fila_excel = len(df_persona) + 2
        
        fmt_total_label = workbook.add_format({'bold': True, 'bg_color': '#E2EFDA', 'border': 1, 'align': 'right'})
        fmt_total_val = workbook.add_format({'bold': True, 'bg_color': '#E2EFDA', 'border': 1, 'align': 'center'})
        
        # Mapeo de personal a rol
        rol_map = df_persona.index.to_series().map(df_personal.set_index('Nombre')['rol'])

        categorias = [
            ("dia planta", "Planta", ["D", "G"]),
            ("dia resi", "Residente", ["D", "G"]),
            ("noche planta", "Planta", ["N", "G"]),
            ("noche resi", "Residente", ["N", "G"])
        ]

        for label, rol_buscado, turnos_buscados in categorias:
            ws_p.write(fila_excel, 0, label, fmt_total_label)
            for col_idx, fecha in enumerate(fechas_unicas):
                count = 0
                for nombre, row in df_persona.iterrows():
                    val = row[fecha]
                    if val in turnos_buscados and rol_map.get(nombre) == rol_buscado:
                        count += 1
                ws_p.write(fila_excel, col_idx + 1, count, fmt_total_val)
            fila_excel += 1

        # Formato gris para F, LAR, LPP en Vista por Personal
        gray_fmt = workbook.add_format({'bg_color': '#F2F2F2', 'font_color': '#7F7F7F', 'border': 1, 'align': 'center'})
        for row_num in range(1, len(df_persona) + 1):
            for col_num in range(1, len(fechas_unicas) + 1):
                val = df_persona.iloc[row_num-1, col_num-1]
                if val in ["F", "LAR", "LPP", "LM"]:
                    ws_p.write(row_num, col_num, val, gray_fmt)

        df_reporte.to_excel(writer, sheet_name='Reporte de Horas', index=False)

    print("¡Excel generado con éxito! Archivo:", file_name)

def generar_y_exportar(df_resultados, df_personal, dias_del_bloque, feriados, fecha_inicio, offset_dia, config_turnos, num_semanas, flrs_asignados=None, df_cat_semanas=None):
    df_pivot, fechas_unicas = exportar_excel_data_prep(df_resultados, df_personal)
    df_persona = exportar_excel_vista_personal(df_resultados, df_personal, flrs_asignados)
    df_reporte = generar_reporte(df_resultados, df_personal)
    exportar_excel(df_pivot, df_persona, df_reporte, fechas_unicas, df_resultados, df_personal)
