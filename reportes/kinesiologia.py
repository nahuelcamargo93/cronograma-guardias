import pandas as pd
from datetime import date
import db as database

def exportar_excel_data_prep(df_resultados, config_turnos):
    # --- PIVOTEAR EL CRONOGRAMA ---
    df_excel = df_resultados.copy()
    
    # OPCION C: Desdoblar los turnos "Dia_" en "Mañana_" y "Tarde_" solo para la vista
    filas_extra = []
    indices_a_borrar = []
    for idx, row in df_excel.iterrows():
        if row['Turno'].startswith('Dia_'):
            suffix = row['Turno'].replace('Dia_', '')
            row_m = row.copy()
            row_m['Turno'] = f"Mañana_{suffix}"
            filas_extra.append(row_m)
            row_t = row.copy()
            row_t['Turno'] = f"Tarde_{suffix}"
            filas_extra.append(row_t)
            indices_a_borrar.append(idx)
            
    df_excel = df_excel.drop(indices_a_borrar)
    if filas_extra:
        df_excel = pd.concat([df_excel, pd.DataFrame(filas_extra)], ignore_index=True)
        
    fechas_unicas = df_excel['Fecha'].unique()
    turnos_ordenados = []
    
    # 1. Armar orden de turnos a partir de config_turnos
    # Obtenemos todos los turnos disponibles (Semana y Finde)
    # y los ordenamos por metadata (si tienen el campo orden). 
    # Ya vienen ordenados de db.py (ORDER BY orden) así que el orden de inserción es válido.
    
    # Primero iteramos todo para recolectar
    for tipo in ["Semana", "Finde_Feriado"]:
        for t in config_turnos.get(tipo, {}).keys():
            if t not in turnos_ordenados:
                turnos_ordenados.append(t)
                
    filas_excel = []
    
    # Obtener orden jerárquico real desde db
    rows_p = database.get_connection().execute("SELECT nombre, rol FROM personal").fetchall()
    jerarquia = {}
    rol_orden = {"Jefe": 1, "Coordinador": 2, "Rotativo": 3, "Nocturno": 4}
    for n, r in rows_p:
        jerarquia[n] = rol_orden.get(r, 100)

    for turno_label in turnos_ordenados:
        df_turno = df_excel[df_excel['Turno'] == turno_label]
        
        # Max personas asignadas en este turno en cualquier día
        max_personas_turno = 0
        for fecha in fechas_unicas:
            count = len(df_turno[df_turno['Fecha'] == fecha])
            if count > max_personas_turno:
                max_personas_turno = count
        
        # Si nadie fue asignado a este turno en todo el periodo, ignorarlo (ej. turnos de verano)
        if max_personas_turno == 0:
            continue

        for i in range(max_personas_turno):
            fila = {"Turno": turno_label}
            for fecha in fechas_unicas:
                pers_dia = df_turno[df_turno['Fecha'] == fecha].sort_values(
                    by='Kinesiologo', key=lambda x: x.map(lambda n: jerarquia.get(n, 100))
                )['Kinesiologo'].tolist()
                fila[fecha] = pers_dia[i] if i < len(pers_dia) else ""
            filas_excel.append(fila)

    # --- AGREGAR FILAS DE LICENCIAS (LAR / LPP) ---
    # Dos filas vacías de separación
    filas_excel.append({"Turno": "  "}) 
    filas_excel.append({"Turno": "   "}) 

    fila_lpp = {"Turno": "LPP"}
    fila_lar = {"Turno": "LAR"}

    for fecha in fechas_unicas:
        fecha_dt = date.fromisoformat(fecha)
        
        # Buscar quiénes están de LPP este día
        nombres_lpp = []
        for nombre, rangos in database.LPP.items():
            for ini_s, fin_s in rangos:
                if date.fromisoformat(ini_s) <= fecha_dt <= date.fromisoformat(fin_s):
                    nombres_lpp.append(nombre)
                    break
        fila_lpp[fecha] = "\\n".join(nombres_lpp)

        # Buscar quiénes están de LAR este día
        nombres_lar = []
        for nombre, rangos in database.LAR.items():
            for ini_s, fin_s in rangos:
                if date.fromisoformat(ini_s) <= fecha_dt <= date.fromisoformat(fin_s):
                    nombres_lar.append(nombre)
                    break
        fila_lar[fecha] = "\\n".join(nombres_lar)

    filas_excel.append(fila_lpp)
    filas_excel.append(fila_lar)

    df_pivot = pd.DataFrame(filas_excel).set_index("Turno")

    return df_pivot, fechas_unicas

from data import asignar_horas

def generar_reporte(df_resultados, df_personal, dias_del_bloque, feriados, fecha_inicio, offset_dia, num_semanas):
    # Reporte de control
    df_reporte_horas = df_resultados.copy()
    df_reporte_horas['Horas'] = df_reporte_horas['Turno'].apply(asignar_horas)
    horas_por_persona = df_reporte_horas.groupby('Kinesiologo')['Horas'].sum().reset_index()
    
    fecha_inicio_dt = pd.to_datetime(fecha_inicio)
    resultados_fl = []
    for _, persona in df_personal.iterrows():
        nombre = persona['Nombre']
        dias_bloqueados = set()
        for lics in [database.LPP, database.LAR]:
            for (ini_s, fin_s) in lics.get(nombre, []):
                ini_dt = pd.to_datetime(ini_s)
                fin_dt = pd.to_datetime(fin_s)
                for d in range((fin_dt - ini_dt).days + 1):
                    fecha_iter = ini_dt + pd.Timedelta(days=d)
                    delta = (fecha_iter - fecha_inicio_dt).days
                    if 0 <= delta < dias_del_bloque:
                        dias_bloqueados.add(delta)

        fechas_trabajadas = df_resultados[df_resultados['Kinesiologo'] == nombre]['Fecha'].tolist()

        bloques = []
        bloque_actual = []
        for d in range(dias_del_bloque):
            if d in dias_bloqueados:
                if bloque_actual:
                    bloques.append(bloque_actual)
                    bloque_actual = []
                continue
            
            es_f = ((d + offset_dia) % 7) >= 5 or d in feriados
            if es_f:
                bloque_actual.append(d)
            else:
                if bloque_actual:
                    bloques.append(bloque_actual)
                    bloque_actual = []
        if bloque_actual:
            bloques.append(bloque_actual)

        f_trab_actual = 0
        f_hab_actual = 0
        
        for sem in range(num_semanas):
            s = sem * 7 + (5 - offset_dia) % 7
            dom = sem * 7 + (6 - offset_dia) % 7
            
            # Habile si no hay licencia ni S ni D
            if s not in dias_bloqueados and dom not in dias_bloqueados:
                f_hab_actual += 1
            
            # Trabajado si hay algun turno en S o D
            f_s = (fecha_inicio_dt + pd.Timedelta(days=s)).strftime("%Y-%m-%d")
            f_dom = (fecha_inicio_dt + pd.Timedelta(days=dom)).strftime("%Y-%m-%d")
            if f_s in fechas_trabajadas or f_dom in fechas_trabajadas:
                f_trab_actual += 1

        fl_3_libres = 0
        fl_4_libres = 0
        for bloque in bloques:
            fechas_bloque = [(fecha_inicio_dt + pd.Timedelta(days=d)).strftime("%Y-%m-%d") for d in bloque]
            trabajo_en_bloque = any(f in fechas_trabajadas for f in fechas_bloque)
            if not trabajo_en_bloque:
                if len(bloque) == 3: fl_3_libres += 1
                elif len(bloque) >= 4: fl_4_libres += 1
                    
        horas_acum = persona.get('Horas_Anuales_Previas', 0) + horas_por_persona[horas_por_persona['Kinesiologo'] == nombre]['Horas'].sum()
        
        f_trab_total = persona.get('Findes_Semanas_Previos', 0) + f_trab_actual
        f_hab_total = persona.get('Findes_Habiles_Previos', 10) + f_hab_actual
        indice_carga = round((f_trab_total / f_hab_total) * 100, 1) if f_hab_total > 0 else 0

        resultados_fl.append({
            'Kinesiologo': nombre,
            'Horas_Anuales_Total': horas_acum,
            'Findes_Actual_Trab': f_trab_actual,
            'Findes_Actual_Hab': f_hab_actual,
            'Findes_Trab_Total': f_trab_total,
            'Findes_Hab_Total': f_hab_total,
            'Indice_Carga_Finde': f"{indice_carga}%",
            'FL3_Total_Acum': persona.get('Findes_Largos_3_Previos', 0) + fl_3_libres,
            'FL4_Total_Acum': persona.get('Findes_Largos_4_Previos', 0) + fl_4_libres
        })
        
    df_fl = pd.DataFrame(resultados_fl)
    reporte_final = pd.merge(horas_por_persona, df_fl, on='Kinesiologo', how='left')

    # Renombrar columnas para el Excel
    reporte_final = reporte_final.rename(columns={
        'Horas': 'Horas del cronograma actual',
        'Horas_Anuales_Total': 'Horas totales anuales',
        'Findes_Actual_Trab': 'Fin de semana actual (Trabajados)',
        'Findes_Actual_Hab': 'Fin de semana actual (Hábiles)',
        'Findes_Trab_Total': 'Acumulado (Trabajados)',
        'Findes_Hab_Total': 'Acumulado (Hábiles)',
        'Indice_Carga_Finde': 'Índice de Carga (%)',
        'FL3_Total_Acum': 'Finde largo 3 dias acumulado',
        'FL4_Total_Acum': 'Finde largo 4 dias acumulado'
    })

    # Ordenar columnas
    columnas_orden = [
        'Kinesiologo',
        'Horas del cronograma actual',
        'Horas totales anuales',
        'Fin de semana actual (Trabajados)',
        'Fin de semana actual (Hábiles)',
        'Acumulado (Trabajados)',
        'Acumulado (Hábiles)',
        'Índice de Carga (%)',
        'Finde largo 3 dias acumulado',
        'Finde largo 4 dias acumulado'
    ]
    reporte_final = reporte_final[columnas_orden]
    reporte_final = reporte_final.sort_values(by='Horas del cronograma actual', ascending=False).reset_index(drop=True)

    print("\\nREPORTE DE CONTROL: HORAS Y FINES DE SEMANA")
    print(reporte_final.to_string())
    
    reporte_final.to_csv('Reporte_Horas_Kinesiologia.csv', index=False)
    return reporte_final

def exportar_excel(df_pivot, df_reporte, fechas_unicas, file_name='Cronograma_Servicio_Kinesiologia.xlsx'):
    with pd.ExcelWriter(file_name, engine='xlsxwriter') as writer:
        # --- HOJA 1: CRONOGRAMA ---
        df_pivot.to_excel(writer, sheet_name='Cronograma')
        workbook  = writer.book
        worksheet = writer.sheets['Cronograma']

        header_fmt = workbook.add_format({'bold': True, 'bg_color': '#D7E4BD', 'border': 1, 'align': 'center'})
        cell_fmt = workbook.add_format({'text_wrap': True, 'valign': 'top', 'border': 1, 'font_size': 9})
        uco_fmt = workbook.add_format({'bg_color': '#FFC0CB', 'text_wrap': True, 'valign': 'top', 'border': 1, 'font_size': 9}) # Pink

        colores = {
            "Mañana": '#EBF1DE',
            "Tarde":  '#FEF2CB',
            "Dia":    '#DAEEF3',
            "Noche":  '#E5E0EC'
        }

        worksheet.set_column(0, 0, 18, header_fmt)
        worksheet.set_column(1, len(fechas_unicas), 18, cell_fmt)

        for i, (turno_label, row) in enumerate(df_pivot.iterrows()):
            fila_excel = i + 1
            turno_clean = turno_label.strip().split('_')[0]
            
            if turno_label.strip() in ["LPP", "LAR"]:
                fmt = workbook.add_format({'bg_color': '#F2F2F2', 'italic': True, 'text_wrap': True, 'border': 1, 'valign': 'top', 'font_size': 8})
                altura = 35
            elif turno_label.strip() == "":
                fmt = workbook.add_format({'bg_color': '#FFFFFF', 'border': 0})
                altura = 15
            elif "UCO" in turno_label:
                fmt = uco_fmt
                altura = 20
            else:
                color = colores.get(turno_clean, '#FFFFFF')
                fmt = workbook.add_format({'bg_color': color, 'text_wrap': True, 'border': 1, 'valign': 'top', 'font_size': 9})
                altura = 20
            
            worksheet.set_row(fila_excel, altura, fmt)

        # --- HOJA 2: REPORTE DE HORAS ---
        df_reporte.to_excel(writer, sheet_name='Reporte de Horas', index=False)
        worksheet_rep = writer.sheets['Reporte de Horas']
        
        rep_header_fmt = workbook.add_format({'bold': True, 'bg_color': '#4F81BD', 'font_color': 'white', 'border': 1, 'align': 'center', 'valign': 'vcenter'})
        rep_cell_fmt = workbook.add_format({'border': 1, 'align': 'center', 'valign': 'vcenter', 'font_size': 10})
        name_cell_fmt = workbook.add_format({'bold': True, 'border': 1, 'bg_color': '#F2F2F2', 'font_size': 10})
        
        alt_cell_fmt = workbook.add_format({'bg_color': '#DCE6F1', 'border': 1, 'align': 'center', 'valign': 'vcenter', 'font_size': 10})
        
        worksheet_rep.set_column(0, 0, 25, name_cell_fmt)
        worksheet_rep.set_column(1, 6, 22, rep_cell_fmt)
        
        for col_num, value in enumerate(df_reporte.columns.values):
            worksheet_rep.write(0, col_num, value, rep_header_fmt)
            
        for row_num in range(1, len(df_reporte) + 1):
            fmt = alt_cell_fmt if row_num % 2 == 0 else rep_cell_fmt
            for col_num in range(1, len(df_reporte.columns)):
                val = df_reporte.iloc[row_num-1, col_num]
                worksheet_rep.write(row_num, col_num, val, fmt)

    print("¡Excel generado con éxito! Archivo:", file_name)

def generar_y_exportar(df_resultados, df_personal, dias_del_bloque, feriados_indices, fecha_inicio, offset_dia, config_turnos, num_semanas):
    """Función unificada para generar todo el reporte visual para Kinesiología"""
    df_pivot, fechas_unicas = exportar_excel_data_prep(df_resultados, config_turnos)
    df_reporte = generar_reporte(df_resultados, df_personal, dias_del_bloque, feriados_indices, fecha_inicio, offset_dia, num_semanas)
    exportar_excel(df_pivot, df_reporte, fechas_unicas)
