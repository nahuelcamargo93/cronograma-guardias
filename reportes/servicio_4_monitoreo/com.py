import pandas as pd
from datetime import date, timedelta
from database import queries as database
from reportes.generales.base import BaseReport, col_to_letter

def exportar_excel_data_prep(df_resultados, config_turnos, df_personal=None):
    df_excel = df_resultados.copy()
    
    # Desdoblar turnos si aplica
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
    rol_orden = {"Supervisor Titular": 1, "Supervisor Suplente": 2, "Monitorista": 3}
    for n, r in rows_p: 
        jerarquia[n] = rol_orden.get(r, 100)

    for turno_label in turnos_ordenados:
        df_turno = df_excel[df_excel['Turno'] == turno_label]
        max_p = 0
        for f in fechas_unicas:
            c = len(df_turno[df_turno['Fecha'] == f])
            if c > max_p: 
                max_p = c
         
        if max_p == 0: 
            continue

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

    nombres_personal = set(df_personal['Nombre'].tolist()) if df_personal is not None else None
    for fecha in fechas_unicas:
        fecha_dt = date.fromisoformat(fecha)
        nombres_lpp = [n for n, r in getattr(database, 'LPP', {}).items() if (nombres_personal is None or n in nombres_personal) and any(date.fromisoformat(i) <= fecha_dt <= date.fromisoformat(f) for i, f in r)]
        fila_lpp[fecha] = "\n".join(nombres_lpp)
        nombres_lar = [n for n, r in getattr(database, 'LAR', {}).items() if (nombres_personal is None or n in nombres_personal) and any(date.fromisoformat(i) <= fecha_dt <= date.fromisoformat(f) for i, f in r)]
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

def exportar_excel_vista_personal(df_resultados, df_personal):
    fechas = sorted(df_resultados['Fecha'].unique())
    nombres = sorted(df_personal['Nombre'].tolist())
    
    col_nombre = 'Personal'
    
    filas = []
    for nombre in nombres:
        fila = {col_nombre: nombre}
        for fecha in fechas:
            asig = df_resultados[(df_resultados[col_nombre] == nombre) & (df_resultados['Fecha'] == fecha)]
            if not asig.empty:
                fila[fecha] = asig.iloc[0]['Turno']
            else:
                fecha_dt = date.fromisoformat(fecha)
                es_lar = any(date.fromisoformat(i) <= fecha_dt <= date.fromisoformat(f) for i, f in getattr(database, 'LAR', {}).get(nombre, []))
                es_lpp = any(date.fromisoformat(i) <= fecha_dt <= date.fromisoformat(f) for i, f in getattr(database, 'LPP', {}).get(nombre, []))
                es_lm = any(date.fromisoformat(i) <= fecha_dt <= date.fromisoformat(f) for i, f in getattr(database, 'LM', {}).get(nombre, []))
                es_cm = any(date.fromisoformat(i) <= fecha_dt <= date.fromisoformat(f) for i, f in getattr(database, 'CM', {}).get(nombre, []))
                if es_lar: 
                    fila[fecha] = "LAR"
                elif es_lpp: 
                    fila[fecha] = "LPP"
                elif es_lm:
                    fila[fecha] = "LM"
                elif es_cm:
                    fila[fecha] = "CM"
                else: 
                    fila[fecha] = "F"
        filas.append(fila)
    return pd.DataFrame(filas).set_index(col_nombre)

def generar_vista_agrupada_sheet(report, df_persona, df_personal, fechas_unicas):
    # Asegurar compatibilidad de mayúsculas en las columnas
    df_personal = df_personal.copy()
    if 'categoria' in df_personal.columns:
        df_personal = df_personal.rename(columns={'categoria': 'Categoria'})
    if 'rol' in df_personal.columns:
        df_personal = df_personal.rename(columns={'rol': 'Rol'})
    if 'nombre' in df_personal.columns:
        df_personal = df_personal.rename(columns={'nombre': 'Nombre'})

    ws = report.workbook.add_worksheet('Vista Personal')
    ws.freeze_panes(2, 1) # Inmovilizar cabeceras y nombres de personal
    
    styles = report.styles
    
    # Formato personalizado para el banner del turno
    banner_format = report.workbook.add_format({
        'bold': True,
        'bg_color': '#8DB4E2',   # Azul pizarra suave
        'font_color': '#FFFFFF', # Texto blanco
        'border': 1,
        'align': 'center',
        'valign': 'vcenter',
        'font_size': 11
    })
    
    # Formatos personalizados para SUP y MON (estética premium)
    sup_fmt = report.workbook.add_format({
        'bg_color': '#C6E0B4',  # Verde tonalidad más oscura
        'border': 1, 'align': 'center', 'valign': 'vcenter', 'font_size': 9, 'bold': True
    })
    sup_fmt_week = report.workbook.add_format({
        'bg_color': '#C6E0B4',  # Verde tonalidad más oscura
        'border': 1, 'right': 5, 'align': 'center', 'valign': 'vcenter', 'font_size': 9, 'bold': True
    })
    mon_fmt = report.workbook.add_format({
        'bg_color': '#E2EFDA',  # Verde claro muy suave
        'border': 1, 'align': 'center', 'valign': 'vcenter', 'font_size': 9
    })
    mon_fmt_week = report.workbook.add_format({
        'bg_color': '#E2EFDA',
        'border': 1, 'right': 5, 'align': 'center', 'valign': 'vcenter', 'font_size': 9
    })
    
    # Formato para la letra F de los francos en rojo
    f_fmt = report.workbook.add_format({
        'bg_color': '#D9D9D9',
        'font_color': '#FF0000',  # Letra F roja
        'border': 1,
        'align': 'center',
        'valign': 'vcenter',
        'font_size': 9,
        'bold': True
    })
    f_fmt_week = report.workbook.add_format({
        'bg_color': '#D9D9D9',
        'font_color': '#FF0000',  # Letra F roja
        'border': 1,
        'right': 5,
        'align': 'center',
        'valign': 'vcenter',
        'font_size': 9,
        'bold': True
    })
    
    def escribir_cabeceras_com(ws, r):
        ws.merge_range(r, 0, r + 1, 0, "APELLIDO Y NOMBRE", styles.header_blue)
        ws.set_column(0, 0, 25)
        
        for col_idx, fecha in enumerate(fechas_unicas):
            dt = date.fromisoformat(fecha)
            sigla = report.siglas_dias[dt.weekday()]
            dia_num = f"{dt.day}/{dt.month}"
            
            is_sep = (dt.weekday() == 6)
            is_weekend = (dt.weekday() >= 5)
            is_holiday = (fecha in report.feriados)
            is_dark = is_weekend or is_holiday
            
            if is_dark:
                fmt_h1 = styles.header_dark_blue_week if is_sep else styles.header_dark_blue
                fmt_h2 = styles.header_dark_light_week if is_sep else styles.header_dark_light
            else:
                fmt_h1 = styles.header_blue_week if is_sep else styles.header_blue
                fmt_h2 = styles.header_light_week if is_sep else styles.header_light

            ws.write(r, 1 + col_idx, sigla, fmt_h1)
            ws.write(r + 1, 1 + col_idx, dia_num, fmt_h2)
            ws.set_column(1 + col_idx, 1 + col_idx, 6)

        # Columna de separación vacía
        sep_col = len(fechas_unicas) + 1
        ws.set_column(sep_col, sep_col, 2)

        # Nuevas columnas de totales
        h_col = len(fechas_unicas) + 2
        fs_col = len(fechas_unicas) + 3
        
        ws.merge_range(r, h_col, r + 1, h_col, "HORAS TRABAJADAS", styles.header_blue)
        ws.set_column(h_col, h_col, 15)
        
        ws.merge_range(r, fs_col, r + 1, fs_col, "FS TRABAJADOS", styles.header_blue)
        ws.set_column(fs_col, fs_col, 15)

    categorias_config = [
        ('A', 'Turno 00hs a 06hs'),
        ('B', 'Turno 06hs a 12hs'),
        ('C', 'Turno 12hs a 18hs'),
        ('D', 'Turno 18hs a 24hs')
    ]
    
    row_ex = 0
    for cat_code, banner_label in categorias_config:
        # Filtrar personas que pertenecen a esta categoría (por categoría base o reglas de turnos habilitados)
        rol_orden = {
            "Supervisor Titular": 1,
            "Supervisor Suplente": 2,
            "Monitorista": 3
        }
        
        indices_cat = []
        for idx, p in df_personal.iterrows():
            # Exclusiones explícitas por persona/bloque
            if p['Nombre'] == "BRIZUELA Irma" and cat_code == 'B':
                continue
            if p['Nombre'] == "OJEDA Miriam" and cat_code != 'B':
                continue
                
            if p['Categoria'] == cat_code:
                indices_cat.append(idx)
            else:
                # Verificar si tiene reglas y puestos que habilitan turnos de esta categoría
                puestos_hab = p.get('puestos_habilitados', [])
                if isinstance(puestos_hab, set):
                    puestos_hab = list(puestos_hab)
                elif not isinstance(puestos_hab, list):
                    puestos_hab = []
                
                reglas = p.get('reglas', {})
                excluir_turnos = []
                if isinstance(reglas, dict) and 'EXCLUIR_TURNOS' in reglas:
                    excluir_rules = reglas['EXCLUIR_TURNOS']
                    if isinstance(excluir_rules, list) and len(excluir_rules) > 0:
                        excluir_turnos = excluir_rules[0].get('turnos', [])
                        
                cat_shifts = {
                    'A': ["00-06_Monitorista", "00-06_Supervisor", "00-06_Administrativo"],
                    'B': ["06-12_Monitorista", "06-12_Supervisor", "06-12_Administrativo"],
                    'C': ["12-18_Monitorista", "12-18_Supervisor", "12-18_Administrativo"],
                    'D': ["18-24_Monitorista", "18-24_Supervisor", "18-24_Administrativo"]
                }.get(cat_code, [])
                
                elegible = False
                for shift in cat_shifts:
                    puesto_shift = shift.split('_')[1]
                    if puesto_shift in puestos_hab and shift not in excluir_turnos:
                        elegible = True
                        break
                if elegible:
                    indices_cat.append(idx)
                            
        personas_cat = df_personal.loc[indices_cat].copy()
        if personas_cat.empty:
            continue
            
        def get_sort_key(row):
            if row['Nombre'] == "OJEDA Miriam":
                return 1000
            return rol_orden.get(row['Rol'], 100)
            
        personas_cat['sort_key'] = personas_cat.apply(get_sort_key, axis=1)
        personas_cat = personas_cat.sort_values(by=['sort_key', 'Nombre'])
        
        # 1. Cabecera del bloque (Días y Números)
        escribir_cabeceras_com(ws, row_ex)
        
        # 2. Fila Banner del Turno
        ws.merge_range(row_ex + 2, 0, row_ex + 2, len(fechas_unicas) + 3, banner_label.upper(), banner_format)
        ws.set_row(row_ex + 2, 24)
        
        # 3. Filas de personal
        curr_row = row_ex + 3
        mon_counts = [0] * len(fechas_unicas)
        
        for _, p in personas_cat.iterrows():
            nombre = p['Nombre']
            ws.write(curr_row, 0, nombre, styles.name_cell)
            
            # Escribir cada día para esta persona
            for col_idx, fecha in enumerate(fechas_unicas):
                val = df_persona.at[nombre, fecha] if nombre in df_persona.index else "F"
                if pd.isna(val) or str(val).lower() == 'nan':
                    val = ""
                val = str(val)
                is_sep = (date.fromisoformat(fecha).weekday() == 6)
                
                # Filtrar el turno para que corresponda a la categoría actual
                cat_prefix_map = {
                    'A': '00-06',
                    'B': '06-12',
                    'C': '12-18',
                    'D': '18-24'
                }
                prefix = cat_prefix_map.get(cat_code, '')
                # Si el valor es una guardia/turno asignado pero no pertenece a esta categoría,
                # para este bloque se considera ocupado en otro turno ("X")
                # Si es un turno asignado pero no pertenece a esta categoría, se considera ocupado en otro turno ("X")
                cat_prefixes = ['00-06', '06-12', '12-18', '18-24']
                is_shift = val not in ["F", "FLR", "LAR", "LPP", "LM", "CM", "", None]
                if is_shift:
                    belongs_to_current = val.startswith(prefix) or (
                        not any(val.startswith(pfx) for pfx in cat_prefixes) and p['Categoria'] == cat_code
                    )
                    if not belongs_to_current:
                        val = "X"
                
                # Traducir / simplificar texto de turno para COM
                if "Supervisor" in val:
                    txt = "SUP"
                    fmt = sup_fmt_week if is_sep else sup_fmt
                elif "Administrativo" in val or ("Monitorista" in val and nombre == "OJEDA Miriam"):
                    txt = "ADM"
                    fmt = sup_fmt_week if is_sep else sup_fmt
                elif "Monitorista" in val:
                    txt = "MON"
                    fmt = mon_fmt_week if is_sep else mon_fmt
                    # Incrementar conteo de monitoristas para esta columna
                    mon_counts[col_idx] += 1
                elif val == "FLR":
                    txt = "FLR"
                    fmt = styles.dark_grey_cell_week if is_sep else styles.dark_grey_cell
                elif val == "F":
                    txt = "F"
                    fmt = f_fmt_week if is_sep else f_fmt
                elif val == "X":
                    txt = "X"
                    fmt = styles.cell_week if is_sep else styles.cell
                elif val in ["LAR", "LPP", "LM", "CM"]:
                    txt = val
                    fmt = styles.grey_cell_week if is_sep else styles.grey_cell
                else:
                    txt = ""
                    fmt = styles.cell_week if is_sep else styles.cell
                
                ws.write(curr_row, col_idx + 1, txt, fmt)
            
            # Calcular fórmulas
            end_col_let = col_to_letter(len(fechas_unicas))
            formula_horas = f'=(COUNTIF(B{curr_row+1}:{end_col_let}{curr_row+1}, "SUP") + COUNTIF(B{curr_row+1}:{end_col_let}{curr_row+1}, "ADM") + COUNTIF(B{curr_row+1}:{end_col_let}{curr_row+1}, "MON")) * 6'
            
            weekend_cols = []
            for col_idx, fecha in enumerate(fechas_unicas):
                dt = date.fromisoformat(fecha)
                if dt.weekday() >= 5:
                    weekend_cols.append(col_to_letter(col_idx + 1))
            
            if weekend_cols:
                formula_fs = "=" + "+".join(f'({col_let}{curr_row+1}="SUP")+({col_let}{curr_row+1}="ADM")+({col_let}{curr_row+1}="MON")' for col_let in weekend_cols)
            else:
                formula_fs = "=0"
                
            # Escribir fórmulas en las columnas nuevas
            ws.write_formula(curr_row, len(fechas_unicas) + 2, formula_horas, styles.cell)
            ws.write_formula(curr_row, len(fechas_unicas) + 3, formula_fs, styles.cell)
            
            curr_row += 1
            
        # 4. Fila de Total Monitoristas
        ws.write(curr_row, 0, "TOTAL MONITORISTAS", styles.total_label)
        for col_idx, fecha in enumerate(fechas_unicas):
            is_sep = (date.fromisoformat(fecha).weekday() == 6)
            fmt = styles.total_val_week if is_sep else styles.total_val
            ws.write(curr_row, col_idx + 1, mon_counts[col_idx], fmt)
            
        # Formatear celdas de las columnas extras en la fila de totales como vacías
        ws.write(curr_row, len(fechas_unicas) + 2, "", styles.total_val)
        ws.write(curr_row, len(fechas_unicas) + 3, "", styles.total_val)
            
        curr_row += 1
            
        # Actualizar puntero y agregar fila en blanco de separación
        row_ex = curr_row
        ws.set_row(row_ex, 15)
        row_ex += 1
        
    if report.crono_id is not None:
        ws.write(row_ex + 1, 0, "ID Cronograma:", report.styles.total_label)
        ws.write(row_ex + 1, 1, report.crono_id, report.styles.total_val)


def calcular_metricas_fin_de_semana_com(df_resultados, df_personal, dias_del_bloque, feriados_indices, fecha_inicio):
    from database.connection import get_connection
    from database.queries import obtener_feriados
    data_feriados = obtener_feriados(servicio_id=4)
    
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
    
    # 1. Metricas del mes actual
    fs_trabajado_mes = {n: 0 for n in nombres}
    medio_fs_trabajado_mes = {n: 0 for n in nombres}
    feriados_trabajados_mes = {n: 0 for n in nombres}
    
    # Helper to calculate metrics for a set of guardias
    def calcular_para_guardias(guardias, fi_dt, ff_dt, f_set):
        weekends_worked = {}
        for g in guardias:
            f_str = g['fecha']
            dt = date.fromisoformat(f_str)
            if fi_dt <= dt <= ff_dt:
                wd = dt.weekday()
                if wd in (5, 6):
                    iso_yr, iso_wk, _ = dt.isocalendar()
                    weekends_worked.setdefault((iso_yr, iso_wk), set()).add(wd)
                    
        fs_t = 0
        medio_fs_t = 0
        for week_key, wds in weekends_worked.items():
            if 5 in wds and 6 in wds:
                fs_t += 1
            else:
                medio_fs_t += 1
                
        feriados_t = len(set(g['fecha'] for g in guardias if g['fecha'] in f_set))
        return fs_t, medio_fs_t, feriados_t

    # Guardias del mes actual
    for nombre in nombres:
        df_emp = df_resultados[df_resultados['Personal'] == nombre]
        guardias_mes = []
        for _, row in df_emp.iterrows():
            guardias_mes.append({
                'fecha': row['Fecha'],
                'turno': row['Turno']
            })
        
        fs_t, medio_fs_t, feriados_t = calcular_para_guardias(guardias_mes, fecha_inicio_dt, fecha_fin_dt, feriados_set)
        fs_trabajado_mes[nombre] = fs_t
        medio_fs_trabajado_mes[nombre] = medio_fs_t
        feriados_trabajados_mes[nombre] = feriados_t
        
    # 2. Metricas historicas
    hist_fs_trabajado = {n: fs_trabajado_mes[n] for n in nombres}
    hist_medio_fs_trabajado = {n: medio_fs_trabajado_mes[n] for n in nombres}
    hist_feriados = {n: feriados_trabajados_mes[n] for n in nombres}
    
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
            
            # Guardias de este cronograma para COM (servicio_id = 4)
            cursor.execute("""
                SELECT g.nombre, g.fecha, g.turno
                FROM guardias g
                JOIN personal p ON g.nombre = p.nombre
                WHERE g.cronograma_id = ? AND p.servicio_id = 4
            """, (cron_id,))
            guardias_cron = cursor.fetchall()
            
            guardias_by_emp = {nombre: [] for nombre in nombres}
            for nombre, fecha, turno in guardias_cron:
                if nombre in guardias_by_emp:
                    guardias_by_emp[nombre].append({
                        'fecha': fecha,
                        'turno': turno
                    })
                    
            for nombre in nombres:
                fs_t, medio_fs_t, feriados_t = calcular_para_guardias(guardias_by_emp[nombre], fi_dt, ff_dt, feriados_set_completo)
                hist_fs_trabajado[nombre] += fs_t
                hist_medio_fs_trabajado[nombre] += medio_fs_t
                hist_feriados[nombre] += feriados_t
                
    return hist_fs_trabajado, hist_medio_fs_trabajado, hist_feriados

def generar_reporte_resumen_com_sheet(report, df_reporte, df_personal, sheet_name='Reporte'):
    # Asegurar compatibilidad de mayúsculas en las columnas
    df_personal = df_personal.copy()
    if 'categoria' in df_personal.columns:
        df_personal = df_personal.rename(columns={'categoria': 'Categoria'})
    if 'rol' in df_personal.columns:
        df_personal = df_personal.rename(columns={'rol': 'Rol'})
    if 'nombre' in df_personal.columns:
        df_personal = df_personal.rename(columns={'nombre': 'Nombre'})

    ws = report.workbook.add_worksheet(sheet_name)
    ws.freeze_panes(2, 1) # Inmovilizar cabeceras y nombres
    
    styles = report.styles
    
    # Formato personalizado para el banner del turno
    banner_format = report.workbook.add_format({
        'bold': True,
        'bg_color': '#8DB4E2',   # Azul pizarra suave
        'font_color': '#FFFFFF', # Texto blanco
        'border': 1,
        'align': 'center',
        'valign': 'vcenter',
        'font_size': 11
    })
    
    # Configurar anchos de columna
    ws.set_column(0, 0, 25) # APELLIDO Y NOMBRE
    ws.set_column(1, 1, 15) # HORAS TOTALES
    ws.set_column(2, 2, 15) # FS TRABAJADO
    ws.set_column(3, 3, 18) # 1/2 FS TRABAJADO
    ws.set_column(4, 4, 20) # FERIADOS TRABAJADOS
    
    df_rep_indexed = df_reporte.set_index('Personal')
    
    categorias_config = [
        ('A', 'Turno 00hs a 06hs'),
        ('B', 'Turno 06hs a 12hs'),
        ('C', 'Turno 12hs a 18hs'),
        ('D', 'Turno 18hs a 24hs')
    ]
    
    row_ex = 0
    for cat_code, banner_label in categorias_config:
        # Filtrar personas que pertenecen a esta categoría
        indices_cat = []
        for idx, p in df_personal.iterrows():
            # Exclusiones explícitas por persona/bloque
            if p['Nombre'] == "BRIZUELA Irma" and cat_code == 'B':
                continue
            if p['Nombre'] == "OJEDA Miriam" and cat_code != 'B':
                continue
                
            if p['Categoria'] == cat_code:
                indices_cat.append(idx)
            else:
                # Verificar si tiene reglas y puestos que habilitan turnos de esta categoría
                puestos_hab = p.get('puestos_habilitados', [])
                if isinstance(puestos_hab, set):
                    puestos_hab = list(puestos_hab)
                elif not isinstance(puestos_hab, list):
                    puestos_hab = []
                
                reglas = p.get('reglas', {})
                excluir_turnos = []
                if isinstance(reglas, dict) and 'EXCLUIR_TURNOS' in reglas:
                    excluir_rules = reglas['EXCLUIR_TURNOS']
                    if isinstance(excluir_rules, list) and len(excluir_rules) > 0:
                        excluir_turnos = excluir_rules[0].get('turnos', [])
                        
                cat_shifts = {
                    'A': ["00-06_Monitorista", "00-06_Supervisor", "00-06_Administrativo"],
                    'B': ["06-12_Monitorista", "06-12_Supervisor", "06-12_Administrativo"],
                    'C': ["12-18_Monitorista", "12-18_Supervisor", "12-18_Administrativo"],
                    'D': ["18-24_Monitorista", "18-24_Supervisor", "18-24_Administrativo"]
                }.get(cat_code, [])
                
                elegible = False
                for shift in cat_shifts:
                    puesto_shift = shift.split('_')[1]
                    if puesto_shift in puestos_hab and shift not in excluir_turnos:
                        elegible = True
                        break
                if elegible:
                    indices_cat.append(idx)
                            
        personas_cat = df_personal.loc[indices_cat].copy()
        if personas_cat.empty:
            continue
            
        rol_orden = {
            "Supervisor Titular": 1,
            "Supervisor Suplente": 2,
            "Monitorista": 3
        }
        
        def get_sort_key(row):
            if row['Nombre'] == "OJEDA Miriam":
                return 1000
            return rol_orden.get(row['Rol'], 100)
            
        personas_cat['sort_key'] = personas_cat.apply(get_sort_key, axis=1)
        personas_cat = personas_cat.sort_values(by=['sort_key', 'Nombre'])
        
        # 1. Cabeceras del bloque
        ws.write(row_ex, 0, "APELLIDO Y NOMBRE", styles.header_blue)
        ws.write(row_ex, 1, "HORAS TOTALES", styles.header_blue)
        ws.write(row_ex, 2, "FS TRABAJADO", styles.header_blue)
        ws.write(row_ex, 3, "1/2 FS TRABAJADO", styles.header_blue)
        ws.write(row_ex, 4, "FERIADOS TRABAJADOS", styles.header_blue)
        
        # 2. Fila Banner del Turno
        ws.merge_range(row_ex + 1, 0, row_ex + 1, 4, banner_label.upper(), banner_format)
        ws.set_row(row_ex + 1, 24)
        
        # 3. Filas de personal
        curr_row = row_ex + 2
        for _, p in personas_cat.iterrows():
            nombre = p['Nombre']
            ws.write(curr_row, 0, nombre, styles.name_cell)
            
            # Buscar datos en el reporte consolidado
            if nombre in df_rep_indexed.index:
                h_tot = int(df_rep_indexed.at[nombre, 'Horas Totales'])
                fs_t = int(df_rep_indexed.at[nombre, 'FS_Trabajado'])
                medio_fs = int(df_rep_indexed.at[nombre, 'Medio_FS_Trabajado'])
                feriados_t = int(df_rep_indexed.at[nombre, 'Feriados_Trabajados'])
            else:
                h_tot, fs_t, medio_fs, feriados_t = 0, 0, 0, 0
                
            ws.write(curr_row, 1, h_tot, styles.cell)
            ws.write(curr_row, 2, fs_t, styles.cell)
            ws.write(curr_row, 3, medio_fs, styles.cell)
            ws.write(curr_row, 4, feriados_t, styles.cell)
            
            curr_row += 1
            
        # Actualizar puntero y agregar fila en blanco de separación
        row_ex = curr_row
        ws.set_row(row_ex, 15)
        row_ex += 1
        
    if report.crono_id is not None:
        ws.write(row_ex + 1, 0, "ID Cronograma:", report.styles.total_label)
        ws.write(row_ex + 1, 1, report.crono_id, report.styles.total_val)

def exportar_excel(df_pivot, df_persona, fechas_unicas, df_resultados, df_personal, dias_del_bloque, feriados_indices, fecha_inicio, offset_dia, file_name='Cronograma_Servicio_COM.xlsx', crono_id=None):
    report = BaseReport(file_name, feriados=feriados_indices, fecha_inicio=fecha_inicio, crono_id=crono_id)
    
    # 1. Nueva Hoja Agrupada y Ordenada
    generar_vista_agrupada_sheet(report, df_persona, df_personal, fechas_unicas)
    
    # 2. Reporte de Horas
    from reportes.generales.base import calcular_resumen_estandar, asignar_horas_base
    df_reporte = calcular_resumen_estandar(df_resultados, df_personal, dias_del_bloque, feriados_indices, fecha_inicio, offset_dia, func_horas=asignar_horas_base)
    
    # Calcular métricas de fin de semana y feriados personalizadas para COM
    fs_trab, medio_fs, feriados_t = calcular_metricas_fin_de_semana_com(
        df_resultados, df_personal, dias_del_bloque, feriados_indices, fecha_inicio
    )
    
    df_reporte['FS_Trabajado'] = df_reporte['Personal'].map(fs_trab)
    df_reporte['Medio_FS_Trabajado'] = df_reporte['Personal'].map(medio_fs)
    df_reporte['Feriados_Trabajados'] = df_reporte['Personal'].map(feriados_t)
    
    generar_reporte_resumen_com_sheet(report, df_reporte, df_personal, sheet_name='Reporte')

    report.close()

def generar_y_exportar(df_resultados, df_personal, dias_del_bloque, feriados_indices, fecha_inicio, offset_dia, config_turnos, num_semanas, file_name=None, crono_id=None):
    if not file_name:
        from utils import obtener_nombre_archivo
        file_name = obtener_nombre_archivo('Cronograma_Servicio_COM.xlsx', fecha_inicio)
    df_pivot, fechas_unicas = exportar_excel_data_prep(df_resultados, config_turnos, df_personal=df_personal)
    df_persona = exportar_excel_vista_personal(df_resultados, df_personal)
    exportar_excel(df_pivot, df_persona, fechas_unicas, df_resultados, df_personal, dias_del_bloque, feriados_indices, fecha_inicio, offset_dia, file_name=file_name, crono_id=crono_id)

