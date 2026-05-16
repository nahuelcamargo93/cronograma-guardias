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
    for l_tipo in ["LPP", "LAR", "LM"]:
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

def exportar_excel_vista_personal(df_resultados, df_personal, flrs_asignados=None):
    from data import FERIADOS
    fechas = sorted(df_resultados['Fecha'].unique().tolist())
    nombres = sorted(df_personal['Nombre'].tolist())
    col_nombre = 'Kinesiologo' if 'Kinesiologo' in df_resultados.columns else 'Personal'
    
    def es_finde(f_str):
        dt = date.fromisoformat(f_str)
        return dt.weekday() >= 5 or f_str in FERIADOS

    filas = []
    for nombre in nombres:
        fila = {"Personal": nombre}
        h_efectivas = 0
        h_licencia = 0
        fs_trabajados = 0
        
        for fecha in fechas:
            asig = df_resultados[(df_resultados[col_nombre] == nombre) & (df_resultados['Fecha'] == fecha)]
            if not asig.empty:
                t = asig.iloc[0]['Turno']
                fila[fecha] = get_abreviacion(t) 
                h_efectivas += asignar_horas_med(t)
                if es_finde(fecha):
                    fs_trabajados += 1
            else:
                # Buscar Licencias
                tipo_lic = ""
                for l_tipo in ["LAR", "LPP", "LM"]:
                    l_dict = getattr(_db, l_tipo, {})
                    if any(r[0] <= fecha <= r[1] for r in l_dict.get(nombre, [])):
                        tipo_lic = l_tipo
                        break
                
                if tipo_lic:
                    fila[fecha] = tipo_lic
                    h_licencia += (36.0 / 7.0) 
                else:
                    fila[fecha] = "F"
        
        h_tot_calc = h_efectivas + h_licencia
        h_obj = df_personal[df_personal['Nombre'] == nombre]['horas_mensuales_reglamentarias'].iloc[0] or 144
        extras = (h_tot_calc - h_obj) / 24.0
        
        fila["Horas Ef."] = int(h_efectivas)
        fila["Horas Lic."] = int(h_licencia + 0.5)
        fila["Horas Tot."] = int(h_tot_calc + 0.5)
        fila["Extras"] = round(extras, 1)
        fila["FS"] = fs_trabajados
        filas.append(fila)
        
    return pd.DataFrame(filas).set_index("Personal")

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

def exportar_excel(df_pivot, df_persona, fechas_unicas, df_resultados, df_personal, dias_del_bloque, feriados, fecha_inicio, offset_dia, file_name='Cronograma_Area_Medica_UTI.xlsx'):
    report = BaseReport(file_name)
    
    # 1. Cronograma
    report.generar_cronograma_sheet(df_pivot, fechas_unicas)
    
    # 2. Vista por Personal
    ext_cols = ["Horas Ef.", "Horas Lic.", "Horas Tot.", "Extras", "FS"]
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

    # 3. Reporte de Horas (Standardized)
    from reportes.base import calcular_resumen_estandar
    df_reporte = calcular_resumen_estandar(df_resultados, df_personal, dias_del_bloque, feriados, fecha_inicio, offset_dia, func_horas=asignar_horas_med)
    report.generar_reporte_resumen_sheet(df_reporte)
    
    report.close()

def generar_y_exportar(df_resultados, df_personal, dias_del_bloque, feriados, fecha_inicio, offset_dia, config_turnos, num_semanas, flrs_asignados=None, df_cat_semanas=None):
    df_pivot, fechas_unicas = exportar_excel_data_prep(df_resultados, df_personal)
    df_persona = exportar_excel_vista_personal(df_resultados, df_personal, flrs_asignados)
    exportar_excel(df_pivot, df_persona, fechas_unicas, df_resultados, df_personal, dias_del_bloque, feriados, fecha_inicio, offset_dia)
