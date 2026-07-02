import pandas as pd
from datetime import date, timedelta
from database import queries as database

def col_to_letter(col):
    letter = ""
    while col >= 0:
        letter = chr(col % 26 + ord('A')) + letter
        col = col // 26 - 1
    return letter

def asignar_horas_base(turno):
    """Fallback simple para asignar horas si el servicio no provee uno."""
    try:
        with database.get_connection() as conn:
            row = conn.execute("SELECT horas FROM turnos_config WHERE nombre = ?", (turno,)).fetchone()
            if row is not None:
                return row[0]
    except Exception:
        pass

    if turno.startswith("Noche") or turno.startswith("Dia"):
        horas_val = 12
    elif "24" in turno and "-" not in turno:
        horas_val = 12
    else:
        horas_val = 6

    print(f"⚠️ [REPORTE] Advertencia: El turno '{turno}' no se encontró en 'turnos_config' o falló la consulta a la BD. Usando fallback heurístico de {horas_val} horas. Verifique la base de datos.")
    return horas_val

def calcular_resumen_estandar(df_resultados, df_personal, dias_del_bloque, feriados_indices, fecha_inicio, offset_dia, func_horas=None):
    if func_horas is None: func_horas = asignar_horas_base
    fecha_inicio_dt = pd.to_datetime(fecha_inicio)
    
    # Convertir feriados_indices (que pueden ser strings o ints) a un set de strings
    feriados_set = set()
    if feriados_indices:
        for f in feriados_indices:
            if isinstance(f, int):
                f_str = (fecha_inicio_dt + pd.Timedelta(days=f)).strftime("%Y-%m-%d")
                feriados_set.add(f_str)
            else:
                feriados_set.add(str(f))
    
    es_descanso = []
    for d in range(dias_del_bloque):
        fecha_d = (fecha_inicio_dt + pd.Timedelta(days=d)).strftime("%Y-%m-%d")
        es_f = ((d + offset_dia) % 7) >= 5 or fecha_d in feriados_set
        es_descanso.append(es_f)
        
    bloques = []; b_act = []
    for d in range(dias_del_bloque):
        if es_descanso[d]: b_act.append(d)
        else:
            if b_act: bloques.append(b_act); b_act = []
    if b_act: bloques.append(b_act)

    day_to_block_len = {}
    for b in bloques:
        for d in b:
            day_to_block_len[d] = len(b)

    # 1. Horas Actuales
    df_res = df_resultados.copy()
    df_res['Horas'] = df_res['Turno'].apply(func_horas)
    horas_actuales = df_res.groupby('Personal')['Horas'].sum()
    
    # 1b. Noches Actuales
    noches_actuales = df_res[df_res['Turno'].str.contains('Noche', case=False, na=False)].groupby('Personal').size()
    
    # 2. Fines de Semana Actuales
    findes_actuales = {n: 0 for n in df_personal['Nombre']}
    for nombre in df_personal['Nombre']:
        semanas_con_finde_trabajado = set()
        df_pers = df_res[df_res['Personal'] == nombre]
        for _, row in df_pers.iterrows():
            dt = pd.to_datetime(row['Fecha'])
            delta = (dt - fecha_inicio_dt).days
            if (dt.weekday() >= 5) and (day_to_block_len.get(delta, 0) <= 2):
                lunes_dt = dt - pd.Timedelta(days=dt.weekday())
                semanas_con_finde_trabajado.add(lunes_dt.strftime("%Y-%m-%d"))
        findes_actuales[nombre] = len(semanas_con_finde_trabajado)

    # 3. FSL3 y FSL4 Actuales
    fsl3_act = {n: 0 for n in df_personal['Nombre']}
    fsl4_act = {n: 0 for n in df_personal['Nombre']}
    for nombre in df_personal['Nombre']:
        fechas_p = set(df_res[df_res['Personal'] == nombre]['Fecha'])
        for b in bloques:
            fechas_b = [(fecha_inicio_dt + pd.Timedelta(days=d)).strftime("%Y-%m-%d") for d in b]
            if any(f in fechas_p for f in fechas_b):
                if len(b) == 3: fsl3_act[nombre] += 1
                elif len(b) >= 4: fsl4_act[nombre] += 1

    # 4. Consolidación
    resumen = []
    
    def _safe_float(val, default=0.0):
        if val is None or pd.isna(val):
            return default
        try:
            return float(val)
        except Exception:
            return default

    for _, p in df_personal.iterrows():
        nombre = p['Nombre']
        h_act = horas_actuales.get(nombre, 0)
        h_prev = _safe_float(p.get('horas_anuales_previas'), 0.0)
        h_tot = h_prev + h_act
        
        # Horas Posibles Historico (desde su primer registro en DB)
        h_reg_mensual = _safe_float(p.get('horas_mensuales_reglamentarias'), 144.0)
        f_ini_hist = p.get('fecha_inicio_historial')
        if f_ini_hist:
            dt_ini_hist = pd.to_datetime(f_ini_hist)
            meses_diff = (fecha_inicio_dt.year - dt_ini_hist.year) * 12 + (fecha_inicio_dt.month - dt_ini_hist.month)
            h_posibles_prev = max(0, meses_diff) * h_reg_mensual
        else:
            h_posibles_prev = 0
        
        # Horas Posibles Actuales (Reglamentarias pro-rata licencias)
        # Licencias en el bloque actual
        dias_lic = 0
        for l_tipo in ["LAR", "LPP", "LM", "CM"]:
            l_dict = getattr(database, l_tipo, {})
            for r in l_dict.get(nombre, []):
                l_ini = pd.to_datetime(r[0]); l_fin = pd.to_datetime(r[1])
                b_ini = fecha_inicio_dt; b_fin = fecha_inicio_dt + pd.Timedelta(days=dias_del_bloque-1)
                inter_ini = max(l_ini, b_ini); inter_fin = min(l_fin, b_fin)
                if inter_ini <= inter_fin:
                    dias_lic += (inter_fin - inter_ini).days + 1
        
        # Pro-rata del bloque actual por días reales (no asumir 30 días fijos)
        # Horas/día = h_reg_mensual / 30, multiplicado por los días hábiles (sin licencia) del bloque
        h_posibles_bloque = (h_reg_mensual / 30.0) * (dias_del_bloque - dias_lic)
        if h_posibles_bloque < 0: h_posibles_bloque = 0
        
        h_posibles_tot = h_posibles_prev + h_posibles_bloque
        
        carga = (h_tot / h_posibles_tot * 100) if h_posibles_tot > 0 else 0
        
        resumen.append({
            'Personal': nombre,
            'Horas Totales': int(h_tot + 0.5),
            'Horas Posibles': int(h_posibles_tot + 0.5),
            'Carga Horaria': f"{round(carga, 1)}%",
            'FS': int(_safe_float(p.get('findes_semanas_previos'), 0.0) + findes_actuales.get(nombre, 0)),
            'FSL3': int(_safe_float(p.get('findes_largos_3_previos'), 0.0) + fsl3_act.get(nombre, 0)),
            'FSL4': int(_safe_float(p.get('findes_largos_4_previos'), 0.0) + fsl4_act.get(nombre, 0)),
            'N': int(_safe_float(p.get('noches_previas'), 0.0) + noches_actuales.get(nombre, 0))
        })
        
    return pd.DataFrame(resumen).sort_values(by='Carga Horaria', ascending=False)

class ReportStyles:
    def __init__(self, workbook):
        self.workbook = workbook
        
        # --- COLORES Y FORMATOS ---
        # Cabeceras principales (Azul)
        self.header_blue = workbook.add_format({
            'bold': True, 'bg_color': '#BDD7EE', 'border': 1, 'align': 'center', 'valign': 'vcenter'
        })
        self.header_blue_week = workbook.add_format({
            'bold': True, 'bg_color': '#BDD7EE', 'border': 1, 'right': 5, 'align': 'center', 'valign': 'vcenter'
        })
        
        # Cabeceras secundarias (Azul claro)
        self.header_light = workbook.add_format({
            'bold': True, 'bg_color': '#DDEBF7', 'border': 1, 'align': 'center', 'valign': 'vcenter', 'font_size': 9
        })
        self.header_light_week = workbook.add_format({
            'bold': True, 'bg_color': '#DDEBF7', 'border': 1, 'right': 5, 'align': 'center', 'valign': 'vcenter', 'font_size': 9
        })
        
        # Cabeceras oscuras para S/D y Feriados
        self.header_dark_blue = workbook.add_format({
            'bold': True, 'bg_color': '#8DB4E2', 'border': 1, 'align': 'center', 'valign': 'vcenter'
        })
        self.header_dark_blue_week = workbook.add_format({
            'bold': True, 'bg_color': '#8DB4E2', 'border': 1, 'right': 5, 'align': 'center', 'valign': 'vcenter'
        })
        self.header_dark_light = workbook.add_format({
            'bold': True, 'bg_color': '#B8CCE4', 'border': 1, 'align': 'center', 'valign': 'vcenter', 'font_size': 9
        })
        self.header_dark_light_week = workbook.add_format({
            'bold': True, 'bg_color': '#B8CCE4', 'border': 1, 'right': 5, 'align': 'center', 'valign': 'vcenter', 'font_size': 9
        })
        
        # Nombres de personal (Salmón/Naranja)
        self.name_cell = workbook.add_format({
            'bold': True, 'bg_color': '#FCE4D6', 'border': 1, 'valign': 'vcenter'
        })
        
        # Celdas estándar
        self.cell = workbook.add_format({
            'border': 1, 'align': 'center', 'valign': 'vcenter', 'font_size': 9, 'text_wrap': True
        })
        self.cell_week = workbook.add_format({
            'border': 1, 'right': 5, 'align': 'center', 'valign': 'vcenter', 'font_size': 9, 'text_wrap': True
        })
        
        # Totales (Verde claro)
        self.total_label = workbook.add_format({
            'bold': True, 'bg_color': '#E2EFDA', 'border': 1, 'align': 'right'
        })
        self.total_val = workbook.add_format({
            'bold': True, 'bg_color': '#E2EFDA', 'border': 1, 'align': 'center'
        })
        self.total_val_week = workbook.add_format({
            'bold': True, 'bg_color': '#E2EFDA', 'border': 1, 'right': 5, 'align': 'center'
        })
        
        # Licencias y Francos (Gris)
        self.grey_cell = workbook.add_format({
            'bg_color': '#D9D9D9', 'font_color': '#595959', 'border': 1, 'align': 'center', 'valign': 'vcenter', 'font_size': 9, 'text_wrap': True
        })
        self.grey_cell_week = workbook.add_format({
            'bg_color': '#D9D9D9', 'font_color': '#595959', 'border': 1, 'right': 5, 'align': 'center', 'valign': 'vcenter', 'font_size': 9, 'text_wrap': True
        })
        
        # Especiales (Gris oscuro para FLR o similar)
        self.dark_grey_cell = workbook.add_format({
            'bg_color': '#A6A6A6', 'font_color': '#FFFFFF', 'bold': True, 'border': 1, 'align': 'center', 'valign': 'vcenter', 'font_size': 9, 'text_wrap': True
        })
        self.dark_grey_cell_week = workbook.add_format({
            'bg_color': '#A6A6A6', 'font_color': '#FFFFFF', 'bold': True, 'border': 1, 'right': 5, 'align': 'center', 'valign': 'vcenter', 'font_size': 9, 'text_wrap': True
        })

        # Colores de turnos (basados en enfermería)
        self.shift_colors = {
            "M": '#EBF1DE',  # Verde claro
            "T": '#FEF2CB',  # Amarillo claro
            "TN": '#DAEEF3', # Azul claro
            "N": '#E5E0EC',  # Púrpura claro
            "G": '#FFF2CC',  # Oro claro (para guardias de médicos)
            "D": '#EBF1DE',  # Verde (para médicos planta/resi)
        }

    def get_shift_format(self, turno_label, is_week_end=False):
        color = self.shift_colors.get(turno_label, '#FFFFFF')
        fmt_dict = {'bg_color': color, 'border': 1, 'align': 'center', 'valign': 'vcenter', 'font_size': 9, 'text_wrap': True}
        if is_week_end:
            fmt_dict['right'] = 5
        return self.workbook.add_format(fmt_dict)

class BaseReport:
    def __init__(self, file_name, feriados=None, fecha_inicio=None, crono_id=None, servicio_id=None):
        self.crono_id = crono_id
        self.servicio_id = servicio_id
        self.fecha_inicio = fecha_inicio
        self.cronograma_celdas = {}
        
        tiene_infracciones = False
        if crono_id is not None:
            try:
                from database import queries as db_queries
                infrs = db_queries.obtener_infracciones(crono_id)
                if infrs:
                    tiene_infracciones = True
                    import os
                    dir_name = os.path.dirname(file_name)
                    base_name = os.path.basename(file_name)
                    new_base_name = base_name.replace("Cronograma_Servicio_", "cronograma_debugger_").replace("Cronograma_", "cronograma_debugger_")
                    if not new_base_name.startswith("cronograma_debugger_"):
                        new_base_name = "cronograma_debugger_" + new_base_name
                    file_name = os.path.join(dir_name, new_base_name)
            except Exception as e:
                print(f"[BaseReport] Error al chequear infracciones: {e}")
                
        self.file_name = file_name
        self.writer = self._safe_init_writer(file_name)
        self.workbook = self.writer.book
        self.styles = ReportStyles(self.workbook)
        self.siglas_dias = ["L", "M", "Mi", "J", "V", "S", "D"]
        
        # Guardar feriados como strings. Si vienen como ints, necesitamos fecha_inicio.
        self.feriados = set()
        if feriados:
            if fecha_inicio and any(isinstance(f, int) for f in feriados):
                f_ini_dt = pd.to_datetime(fecha_inicio)
                for f in feriados:
                    if isinstance(f, int):
                        self.feriados.add((f_ini_dt + pd.Timedelta(days=f)).strftime("%Y-%m-%d"))
                    else:
                        self.feriados.add(str(f))
            else:
                self.feriados = set(str(f) for f in feriados)
                
        if tiene_infracciones:
            try:
                from reportes.generales.excel_debugger import inyectar_reporte_infracciones
                inyectar_reporte_infracciones(self, crono_id)
            except Exception as e:
                print(f"[BaseReport] Error al inyectar reporte de infracciones: {e}")

    def _safe_init_writer(self, file_name):
        """Intenta inicializar el writer, pidiendo reintento si el archivo está bloqueado."""
        import time
        retries = 0
        while True:
            try:
                return pd.ExcelWriter(file_name, engine='xlsxwriter')
            except PermissionError:
                retries += 1
                if retries > 5:
                    raise PermissionError(f"[ERROR] Operacion cancelada. El archivo '{file_name}' esta abierto en otra aplicacion.")
                print(f"\n[ERROR] No se puede escribir en '{file_name}'.")
                print("   El archivo esta abierto en otra aplicacion (Excel, por ejemplo).")
                print(f"   Por favor, cerralo. Reintentando en 3 segundos... (Intento {retries}/5)")
                time.sleep(3)
            except Exception as e:
                raise e

    def _es_fin_de_semana_sep(self, fecha_str):
        """Retorna True si el día es Domingo (separador de semana)."""
        dt = date.fromisoformat(fecha_str)
        return dt.weekday() == 6

    def escribir_cabeceras_calendario(self, ws, fechas_unicas, start_col=1, col_width=12, start_row=0, use_day_only=False):
        """Escribe las dos filas de cabecera (Día Sigla y Fecha)."""
        for col_idx, fecha in enumerate(fechas_unicas):
            dt = date.fromisoformat(fecha)
            sigla = self.siglas_dias[dt.weekday()]
            dia_num = str(dt.day) if use_day_only else f"{dt.day}/{dt.month}"
            
            is_sep = (dt.weekday() == 6)
            is_weekend = (dt.weekday() >= 5)
            is_holiday = (fecha in self.feriados)
            is_dark = is_weekend or is_holiday
            
            if is_dark:
                fmt_h1 = self.styles.header_dark_blue_week if is_sep else self.styles.header_dark_blue
                fmt_h2 = self.styles.header_dark_light_week if is_sep else self.styles.header_dark_light
            else:
                fmt_h1 = self.styles.header_blue_week if is_sep else self.styles.header_blue
                fmt_h2 = self.styles.header_light_week if is_sep else self.styles.header_light

            ws.write(start_row, start_col + col_idx, sigla, fmt_h1)
            ws.write(start_row + 1, start_col + col_idx, dia_num, fmt_h2)
            ws.set_column(start_col + col_idx, start_col + col_idx, col_width)

    def generar_cronograma_sheet(self, df_pivot, fechas_unicas, sheet_name='Cronograma'):
        ws = self.workbook.add_worksheet(sheet_name)
        ws.freeze_panes(2, 1) # Inmovilizar 2 filas y 1 columna
        
        # Cabecera Lateral
        ws.merge_range(0, 0, 1, 0, "TURNO", self.styles.header_blue)
        ws.set_column(0, 0, 15)
        
        # Cabeceras de Fecha
        self.escribir_cabeceras_calendario(ws, fechas_unicas)
        
        # Pre-procesar información de las filas y mapear etiquetas
        filas_info = []
        row_ex = 2
        for turno_label, row in df_pivot.iterrows():
            turno_mostrar = turno_label
            if self.servicio_id == 1:
                turno_lower = str(turno_label).lower()
                if "mañana" in turno_lower or "maana" in turno_lower:
                    turno_mostrar = "Mañana"
                elif "tarde" in turno_lower:
                    turno_mostrar = "Tarde"
                elif "dia" in turno_lower:
                    turno_mostrar = "Día"
                elif "noche" in turno_lower:
                    turno_mostrar = "Noche"
            elif self.servicio_id == 3:
                turno_lower = str(turno_label).lower()
                if turno_lower.startswith("d_") or turno_lower.startswith("dia"):
                    turno_mostrar = "Día"
                elif turno_lower.startswith("g_") or turno_lower.startswith("guardia"):
                    turno_mostrar = "Guardia"
                elif turno_lower.startswith("n_") or turno_lower.startswith("noche"):
                    turno_mostrar = "Noche"
            
            filas_info.append({
                'row_ex': row_ex,
                'turno_label': turno_label,
                'turno_mostrar': turno_mostrar,
                'row': row
            })
            row_ex += 1

        # Escribir columnas de datos de forma estándar
        for idx_f, f_info in enumerate(filas_info):
            row_num = f_info['row_ex']
            turno_label = f_info['turno_label']
            row = f_info['row']
            
            # Detectar si es frontera inferior (límite entre turnos)
            es_frontera = False
            if self.servicio_id in [1, 3]:
                if idx_f + 1 < len(filas_info):
                    if filas_info[idx_f]['turno_mostrar'] != filas_info[idx_f + 1]['turno_mostrar']:
                        es_frontera = True
                else:
                    es_frontera = True
            
            for col_idx, fecha in enumerate(fechas_unicas):
                val = row[fecha]
                if pd.isna(val) or str(val).lower() == 'nan': val = ""
                val = str(val)
                is_sep = self._es_fin_de_semana_sep(fecha)
                
                # Formato según valor
                if str(turno_label).strip() == "":
                    fmt = self.workbook.add_format({
                        'bg_color': '#FFFFFF',
                        'border': 0
                    })
                elif turno_label in ["LPP", "LAR", "LM", "CM"]:
                    if es_frontera:
                        fmt = self.workbook.add_format({
                            'bg_color': '#D9D9D9', 'font_color': '#595959', 'border': 1, 'align': 'center', 'valign': 'vcenter', 'font_size': 9, 'text_wrap': True,
                            'right': 5 if is_sep else 1, 'bottom': 5
                        })
                    else:
                        fmt = self.styles.grey_cell_week if is_sep else self.styles.grey_cell
                else:
                    if self.servicio_id in [1, 3]:
                        if self.servicio_id == 1:
                            # Colores personalizados para Kinesiología
                            turno_lower = str(turno_label).lower()
                            if "uco" in turno_lower:
                                color = '#FADBD8'
                            elif "uti" in turno_lower:
                                color = '#D5F5E3'
                            elif "especial" in turno_lower:
                                color = '#FCF3CF'
                            elif "noche" in turno_lower:
                                color = '#EBDEF0'
                            else:
                                color = '#FFFFFF'
                        else:
                            # servicio_id == 3
                            base_turno = turno_label.split('_')[0]
                            base_turno_map = {
                                "Dia": "D", "Día": "D",
                                "Noche": "N",
                                "Guardia": "G"
                            }
                            base_letra = base_turno_map.get(base_turno, base_turno)
                            color = self.styles.shift_colors.get(base_letra, '#FFFFFF')
                        
                        fmt_dict = {'bg_color': color, 'border': 1, 'align': 'center', 'valign': 'vcenter', 'font_size': 9, 'text_wrap': True}
                        if is_sep:
                            fmt_dict['right'] = 5
                        if es_frontera:
                            fmt_dict['bottom'] = 5
                        fmt = self.workbook.add_format(fmt_dict)
                    else:
                        # Intentar obtener color de turno
                        base_turno = turno_label.split('_')[0]
                        fmt = self.styles.get_shift_format(base_turno, is_sep)
                
                ws.write(row_num, col_idx + 1, val, fmt)
            
            # Ajustar altura de fila
            if turno_label in ["LPP", "LAR", "LM", "CM"]:
                max_lineas = 1
                for f in fechas_unicas:
                    val_cell = str(row[f]) if not pd.isna(row[f]) else ""
                    cant_lineas = val_cell.count('\n') + 1 if val_cell.strip() else 1
                    if cant_lineas > max_lineas:
                        max_lineas = cant_lineas
                ws.set_row(row_num, max(30, max_lineas * 15))
            elif str(turno_label).strip() == "":
                ws.set_row(row_num, 15)

        # Escribir y/o fusionar celdas en la columna 0 ("Turno")
        if self.servicio_id in [1, 3]:
            i = 0
            n = len(filas_info)
            while i < n:
                curr_mostrar = filas_info[i]['turno_mostrar']
                start_row = filas_info[i]['row_ex']
                
                # Agrupar solo turnos normales consecutivos para la fusión vertical
                if curr_mostrar in ["Mañana", "Tarde", "Día", "Noche", "Guardia"]:
                    j = i + 1
                    while j < n and filas_info[j]['turno_mostrar'] == curr_mostrar:
                        j += 1
                    end_row = filas_info[j-1]['row_ex']
                    
                    fmt_dict_col0 = {
                        'bold': True, 'bg_color': '#BDD7EE', 'border': 1, 'align': 'center', 'valign': 'vcenter', 'bottom': 5
                    }
                    fmt_col0 = self.workbook.add_format(fmt_dict_col0)
                    
                    if start_row < end_row:
                        ws.merge_range(start_row, 0, end_row, 0, curr_mostrar, fmt_col0)
                    else:
                        ws.write(start_row, 0, curr_mostrar, fmt_col0)
                    i = j
                else:
                    # Licencias, filas vacías u otros se escriben individualmente
                    if curr_mostrar.strip() == "":
                        fmt_col0 = self.workbook.add_format({
                            'bg_color': '#FFFFFF',
                            'border': 0
                        })
                    else:
                        es_frontera_lic = False
                        if i + 1 < n:
                            if filas_info[i]['turno_mostrar'] != filas_info[i+1]['turno_mostrar']:
                                es_frontera_lic = True
                        else:
                            es_frontera_lic = True
                            
                        if es_frontera_lic:
                            fmt_col0 = self.workbook.add_format({
                                'bold': True, 'bg_color': '#BDD7EE', 'border': 1, 'align': 'center', 'valign': 'vcenter', 'bottom': 5
                            })
                        else:
                            fmt_col0 = self.styles.header_blue
                        
                    ws.write(start_row, 0, curr_mostrar, fmt_col0)
                    i += 1
        else:
            # Mantener comportamiento original para los demás servicios
            for f_info in filas_info:
                ws.write(f_info['row_ex'], 0, f_info['turno_mostrar'], self.styles.header_blue)
                
        return ws

    def generar_cronograma_semanal_sheet(self, df_pivot, fechas_unicas, df_resultados, df_personal, sheet_name='Cronograma'):
        ws = self.workbook.add_worksheet(sheet_name)
        ws.freeze_panes(1, 1) # Inmovilizar 1 fila y 1 columna
        ws.set_column(0, 0, 15)
        # Columnas de Lunes a Domingo
        for col in range(1, 8):
            ws.set_column(col, col, 15)
            
        def solo_apellido(nombre_completo):
            if not nombre_completo:
                return ""
            lineas = str(nombre_completo).split('\n')
            apellidos = []
            for linea in lineas:
                if not linea.strip():
                    continue
                parte_apellido = linea.split(',')[0].strip()
                if parte_apellido.lower() == "navarro suarez":
                    apellidos.append("Suarez")
                else:
                    primer_ap = parte_apellido.split(' ')[0].strip()
                    apellidos.append(primer_ap)
            return "\n".join(apellidos)
            
        nombres_personal = df_personal['Nombre'].tolist()
        apellidos_validos = sorted(list(set([solo_apellido(n) for n in nombres_personal if n])))
            
        # Determinar el rango total de semanas
        import pandas as pd
        from datetime import datetime, timedelta
        
        fecha_inicio_dt = datetime.strptime(fechas_unicas[0], "%Y-%m-%d")
        fecha_fin_dt = datetime.strptime(fechas_unicas[-1], "%Y-%m-%d")
        
        offset_start = fecha_inicio_dt.weekday() # 0 = Lunes, 6 = Domingo
        lunes_inicio_dt = fecha_inicio_dt - timedelta(days=offset_start)
        
        offset_end = 6 - fecha_fin_dt.weekday()
        domingo_fin_dt = fecha_fin_dt + timedelta(days=offset_end)
        
        # Generar bloques semanales
        semanas = []
        curr_lunes = lunes_inicio_dt
        while curr_lunes <= domingo_fin_dt:
            semanas.append(curr_lunes)
            curr_lunes += timedelta(days=7)
            
        # 1. Fila 0: Fija con las siglas de los días (Lunes a Domingo)
        ws.write(0, 0, "TURNO", self.styles.header_blue)
        for i in range(7):
            sigla = self.siglas_dias[i]
            is_sep = (i == 6)
            fmt_h1 = self.styles.header_blue_week if is_sep else self.styles.header_blue
            ws.write(0, i + 1, sigla, fmt_h1)
            
        row_curr = 1
        grupos_turno = [
            ("Día", ["Dia_Planta", "Dia_Residente"]),
            ("Guardia", ["Guardia_Planta", "Guardia_Residente"]),
            ("Noche", ["Noche_Planta", "Noche_Residente"])
        ]
        
        for sem_idx, lunes_dt in enumerate(semanas):
            # Fila de fechas del bloque semanal (Semana X y fechas d/m)
            ws.write(row_curr, 0, f"Semana {sem_idx + 1}", self.styles.header_light)
            
            dias_semana_fechas = []
            for i in range(7):
                dia_dt = lunes_dt + timedelta(days=i)
                fecha_str = dia_dt.strftime("%Y-%m-%d")
                dias_semana_fechas.append((i + 1, fecha_str, dia_dt))
                
                dia_num = f"{dia_dt.day}/{dia_dt.month}"
                is_sep = (i == 6)
                is_weekend = (dia_dt.weekday() >= 5)
                is_holiday = (fecha_str in self.feriados)
                is_dark = is_weekend or is_holiday
                
                if is_dark:
                    fmt_h2 = self.styles.header_dark_light_week if is_sep else self.styles.header_dark_light
                else:
                    fmt_h2 = self.styles.header_light_week if is_sep else self.styles.header_light
                    
                ws.write(row_curr, i + 1, dia_num, fmt_h2)
                
            row_curr += 1
            
            # Escribir filas de datos
            for grupo_nombre, turnos_grupo in grupos_turno:
                # Mapear color default del grupo
                if grupo_nombre == "Día":
                    color_default = '#EBF1DE' # Verde
                elif grupo_nombre == "Guardia":
                    color_default = '#FFF2CC' # Amarillo/Oro
                else:
                    color_default = '#E5E0EC' # Púrpura
                    
                # Guardar las asignaciones separadas por sub-turno
                sub_turnos_asig = {} # turno_exacto -> col_idx -> list
                max_filas_sub = {} # turno_exacto -> int
                
                for t_exacto in turnos_grupo:
                    sub_turnos_asig[t_exacto] = {}
                    max_filas_sub[t_exacto] = 0
                    
                    for col_idx, fecha_str, dia_dt in dias_semana_fechas:
                        sub_turnos_asig[t_exacto][col_idx] = []
                        if fechas_unicas[0] <= fecha_str <= fechas_unicas[-1]:
                            df_dia = df_resultados[df_resultados['Fecha'] == fecha_str]
                            df_t = df_dia[df_dia['Turno'] == t_exacto]
                            
                            col_nombre = 'Personal' if 'Personal' in df_t.columns else ('Kinesiologo' if 'Kinesiologo' in df_t.columns else '')
                            if col_nombre:
                                df_t = df_t.sort_values(by=col_nombre)
                                for _, r_res in df_t.iterrows():
                                    name_val = r_res[col_nombre]
                                    sub_turnos_asig[t_exacto][col_idx].append({
                                        'nombre': name_val,
                                        'apellido': solo_apellido(name_val),
                                        'turno_exacto': t_exacto
                                    })
                                    
                        if len(sub_turnos_asig[t_exacto][col_idx]) > max_filas_sub[t_exacto]:
                            max_filas_sub[t_exacto] = len(sub_turnos_asig[t_exacto][col_idx])
                            
                    # Asegurar al menos 1 fila si no hay asignaciones para que la grilla exista pintada
                    if max_filas_sub[t_exacto] == 0:
                        max_filas_sub[t_exacto] = 1
                        
                start_row_grupo = row_curr
                
                # Escribir las filas segregadas por sub-turno
                for t_idx, t_exacto in enumerate(turnos_grupo):
                    cant_filas = max_filas_sub[t_exacto]
                    for r_idx in range(cant_filas):
                        ws.set_row(row_curr, 16)
                        for col_idx, fecha_str, dia_dt in dias_semana_fechas:
                            is_sep = (col_idx == 7)
                            
                            # Determinar si es primera/última fila del bloque del turno
                            es_primera_fila = (t_idx == 0 and r_idx == 0)
                            es_ultimo_sub = (t_idx == len(turnos_grupo) - 1)
                            es_ultima_fila = es_ultimo_sub and (r_idx == cant_filas - 1)
                            
                            top_border = 1
                            top_color = '#000000' if es_primera_fila else '#D9D9D9'
                            
                            bottom_border = 5 if es_ultima_fila else 1
                            bottom_color = '#000000' if es_ultima_fila else '#D9D9D9'
                            
                            left_border = 1
                            left_color = '#000000' if col_idx == 1 else '#D9D9D9'
                            
                            right_border = 5 if is_sep else 1
                            right_color = '#000000' if is_sep else '#D9D9D9'
                            
                            # Si cae fuera del rango real
                            if not (fechas_unicas[0] <= fecha_str <= fechas_unicas[-1]):
                                fmt = self.workbook.add_format({
                                    'bg_color': '#D9D9D9',
                                    'top': top_border, 'top_color': top_color,
                                    'bottom': bottom_border, 'bottom_color': bottom_color,
                                    'left': left_border, 'left_color': left_color,
                                    'right': right_border, 'right_color': right_color
                                })
                                ws.write(row_curr, col_idx, "", fmt)
                                continue
                                
                            # Registrar celda para médicos (servicio_id == 3)
                            if self.servicio_id == 3:
                                col_letter = col_to_letter(col_idx)
                                ref_celda = f"'{sheet_name}'!${col_letter}${row_curr + 1}"
                                self.cronograma_celdas.setdefault(fecha_str, []).append((t_exacto, ref_celda))

                            # Si cae dentro
                            lista_asig = sub_turnos_asig[t_exacto][col_idx]
                            if r_idx < len(lista_asig):
                                asig = lista_asig[r_idx]
                                val = asig['apellido']
                                color = color_default
                            else:
                                val = ""
                                color = color_default
                                
                            fmt_dict = {
                                'bg_color': color,
                                'top': top_border, 'top_color': top_color,
                                'bottom': bottom_border, 'bottom_color': bottom_color,
                                'left': left_border, 'left_color': left_color,
                                'right': right_border, 'right_color': right_color,
                                'align': 'center',
                                'valign': 'vcenter',
                                'font_size': 9,
                                'text_wrap': True
                            }
                            
                            fmt = self.workbook.add_format(fmt_dict)
                            ws.write(row_curr, col_idx, val, fmt)
                            
                            # Validar que solo se puedan colocar apellidos mediante menú desplegable
                            ws.data_validation(row_curr, col_idx, row_curr, col_idx, {
                                'validate': 'list',
                                'source': apellidos_validos,
                                'input_title': 'Seleccionar Médico',
                                'input_message': 'Elegí un médico de la lista.',
                                'error_title': 'Médico Inválido',
                                'error_message': 'El apellido ingresado no corresponde a un médico activo.'
                            })
                            
                        row_curr += 1
                        
                end_row_grupo = row_curr - 1
                
                # Escribir y unificar columna 0 ("TURNO")
                fmt_dict_col0 = {
                    'bold': True,
                    'bg_color': '#BDD7EE',
                    'border': 1,
                    'align': 'center',
                    'valign': 'vcenter',
                    'bottom': 5
                }
                fmt_col0 = self.workbook.add_format(fmt_dict_col0)
                
                if start_row_grupo < end_row_grupo:
                    ws.merge_range(start_row_grupo, 0, end_row_grupo, 0, grupo_nombre, fmt_col0)
                else:
                    ws.write(start_row_grupo, 0, grupo_nombre, fmt_col0)
                    
            # Separador entre semanas (dejar 1 fila vacía)
            ws.set_row(row_curr, 15)
            for c in range(8):
                ws.write(row_curr, c, "", self.workbook.add_format({'bg_color': '#FFFFFF', 'border': 0}))
            row_curr += 1
            
        if self.crono_id is not None:
            ws.write(row_curr, 0, "ID Cronograma:", self.styles.total_label)
            ws.write(row_curr, 1, self.crono_id, self.styles.total_val)
            
        return ws

    def generar_vista_personal_sheet(self, df_persona, fechas_unicas, extension_columns=None, label_personal="PERSONAL", sheet_name='Vista por Personal', renombrar_francos=False, formulas=None):
        def solo_apellido(nombre_completo):
            if not nombre_completo:
                return ""
            lineas = str(nombre_completo).split('\n')
            apellidos = []
            for linea in lineas:
                if not linea.strip():
                    continue
                parte_apellido = linea.split(',')[0].strip()
                if parte_apellido.lower() == "navarro suarez":
                    apellidos.append("Suarez")
                else:
                    primer_ap = parte_apellido.split(' ')[0].strip()
                    apellidos.append(primer_ap)
            return "\n".join(apellidos)

        def get_abreviacion(turno):
            mapping = {
                "D_Planta": "D_P", "N_Planta": "N_P", "G_Planta": "G_P",
                "D_Residente": "D_R", "N_Residente": "N_R", "G_Residente": "G_R",
                "Dia_Planta": "D_P", "Noche_Planta": "N_P", "Guardia_Planta": "G_P",
                "Dia_Residente": "D_R", "Noche_Residente": "N_R", "Guardia_Residente": "G_R"
            }
            return mapping.get(turno, turno)

        ws = self.workbook.add_worksheet(sheet_name)
        es_enfermeria_vista_personal = (self.servicio_id == 2 and sheet_name == 'Vista Personal')
        if es_enfermeria_vista_personal:
            ws.freeze_panes(5, 1) # Inmovilizar 5 filas y 1 columna
        else:
            ws.freeze_panes(2, 1) # Inmovilizar 2 filas y 1 columna
        
        end_col_letter = col_to_letter(len(fechas_unicas))
        col_offset = len(fechas_unicas) + 2 # +1 por nombre, +1 por columna en blanco
        
        # Columna en blanco de separación
        ws.set_column(col_offset - 1, col_offset - 1, 2) 

        if es_enfermeria_vista_personal:
            # Title bold style
            title_bold = self.workbook.add_format({'bold': True, 'font_size': 11})
            ws.write(0, 0, "HOSPITAL CENTRAL RAMON CARRILLO", title_bold)
            ws.write(1, 0, "DEPARTAMENTO DE ENFERMERÍA", title_bold)
            ws.write(2, 0, "PLANILLA DE ROTACION: ENFERMERÍA AREA CRITICA", title_bold)
            
            from datetime import date
            MESES = {
                1: "ENERO", 2: "FEBRERO", 3: "MARZO", 4: "ABRIL",
                5: "MAYO", 6: "JUNIO", 7: "JULIO", 8: "AGOSTO",
                9: "SEPTIEMBRE", 10: "OCTUBRE", 11: "NOVIEMBRE", 12: "DICIEMBRE"
            }
            dt_start = date.fromisoformat(self.fecha_inicio) if hasattr(self, 'fecha_inicio') and self.fecha_inicio else date.today()
            mes_str = MESES[dt_start.month]
            anio_str = str(dt_start.year)
            mes_anio_text = f"MES:   {mes_str}     AÑO:     {anio_str}"
            ws.write(2, 14, mes_anio_text, title_bold)
            
            # Cabecera Lateral
            ws.merge_range(3, 0, 4, 0, label_personal, self.styles.header_blue)
            ws.set_column(0, 0, 25)
            
            # Cabeceras de Fecha
            self.escribir_cabeceras_calendario(ws, fechas_unicas, col_width=6, start_row=3, use_day_only=True)
            
            # Columnas de Extensión
            if extension_columns:
                for i, col_name in enumerate(extension_columns):
                    ws.merge_range(3, col_offset + i, 4, col_offset + i, col_name, self.styles.header_blue)
                    ws.set_column(col_offset + i, col_offset + i, 10)
            
            row_ex = 5
        else:
            # Cabecera Lateral
            ws.merge_range(0, 0, 1, 0, label_personal, self.styles.header_blue)
            ws.set_column(0, 0, 25)
            
            # Cabeceras de Fecha (más angostas aquí)
            self.escribir_cabeceras_calendario(ws, fechas_unicas, col_width=6, start_row=0, use_day_only=False)
            
            # Columnas de Extensión (Totales, etc)
            if extension_columns:
                for i, col_name in enumerate(extension_columns):
                    ws.merge_range(0, col_offset + i, 1, col_offset + i, col_name, self.styles.header_blue)
                    ws.set_column(col_offset + i, col_offset + i, 10)
            
            row_ex = 2

        # Formatos especiales para Enfermería Vista Personal (servicio_id == 2 y sheet_name == 'Vista Personal')
        if es_enfermeria_vista_personal:
            # Formatos de fin de semana (azul-gris suave #E8EEF5)
            fmt_finde = self.workbook.add_format({
                'bg_color': '#E8EEF5', 'border': 1, 'align': 'center', 'valign': 'vcenter', 'font_size': 9, 'text_wrap': True
            })
            fmt_finde_week = self.workbook.add_format({
                'bg_color': '#E8EEF5', 'border': 1, 'right': 5, 'align': 'center', 'valign': 'vcenter', 'font_size': 9, 'text_wrap': True
            })
            fmt_turno_finde = self.workbook.add_format({
                'bg_color': '#E8EEF5', 'border': 1, 'bold': True, 'align': 'center', 'valign': 'vcenter', 'font_size': 9, 'text_wrap': True
            })
            fmt_turno_finde_week = self.workbook.add_format({
                'bg_color': '#E8EEF5', 'border': 1, 'right': 5, 'bold': True, 'align': 'center', 'valign': 'vcenter', 'font_size': 9, 'text_wrap': True
            })

            # Formatos de feriados (rosa suave #FADBD8)
            fmt_feriado = self.workbook.add_format({
                'bg_color': '#FADBD8', 'border': 1, 'align': 'center', 'valign': 'vcenter', 'font_size': 9, 'text_wrap': True
            })
            fmt_feriado_week = self.workbook.add_format({
                'bg_color': '#FADBD8', 'border': 1, 'right': 5, 'align': 'center', 'valign': 'vcenter', 'font_size': 9, 'text_wrap': True
            })
            fmt_turno_feriado = self.workbook.add_format({
                'bg_color': '#FADBD8', 'border': 1, 'bold': True, 'align': 'center', 'valign': 'vcenter', 'font_size': 9, 'text_wrap': True
            })
            fmt_turno_feriado_week = self.workbook.add_format({
                'bg_color': '#FADBD8', 'border': 1, 'right': 5, 'bold': True, 'align': 'center', 'valign': 'vcenter', 'font_size': 9, 'text_wrap': True
            })
        for nombre, row in df_persona.iterrows():
            ws.write(row_ex, 0, nombre, self.styles.name_cell)
            
            if es_enfermeria_vista_personal:
                # Pre-procesar valores de la fila
                fechas_vals = []
                for col_idx, fecha in enumerate(fechas_unicas):
                    val = row[fecha]
                    if pd.isna(val) or str(val).lower() == 'nan': val = ""
                    val = str(val)
                    if renombrar_francos and val in ["F", "FLR"]:
                        val = "FS"
                    fechas_vals.append((col_idx, fecha, val))
                
                # Escribir con unificación de licencias y colores personalizados
                i = 0
                n_fechas = len(fechas_unicas)
                while i < n_fechas:
                    col_idx, fecha, val = fechas_vals[i]
                    
                    if val in ["LAR", "LPP", "LM", "CM"]:
                        # Encontrar bloque contiguo de la misma licencia
                        j = i + 1
                        while j < n_fechas and fechas_vals[j][2] == val:
                            j += 1
                        
                        start_col = i + 1
                        end_col = j
                        ultimo_fecha = fechas_vals[j-1][1]
                        ultimo_is_sep = self._es_fin_de_semana_sep(ultimo_fecha)
                        
                        fmt_lic = self.styles.grey_cell_week if ultimo_is_sep else self.styles.grey_cell
                        
                        if start_col < end_col:
                            ws.merge_range(row_ex, start_col, row_ex, end_col, val, fmt_lic)
                        else:
                            ws.write(row_ex, start_col, val, fmt_lic)
                        
                        i = j
                    else:
                        # Celda individual (no licencia)
                        dt = date.fromisoformat(fecha)
                        is_sep = self._es_fin_de_semana_sep(fecha)
                        is_weekend = (dt.weekday() >= 5)
                        is_holiday = (fecha in self.feriados)
                        
                        if is_holiday:
                            if val in ["FS", "FCG"]:
                                fmt = fmt_feriado_week if is_sep else fmt_feriado
                            else:
                                fmt = fmt_turno_feriado_week if is_sep else fmt_turno_feriado
                        elif is_weekend:
                            if val in ["FS", "FCG"]:
                                fmt = fmt_finde_week if is_sep else fmt_finde
                            else:
                                fmt = fmt_turno_finde_week if is_sep else fmt_turno_finde
                        else:
                            # Día hábil normal (todo con fondo blanco)
                            fmt = self.styles.cell_week if is_sep else self.styles.cell
                        
                        ws.write(row_ex, col_idx + 1, val, fmt)
                        i += 1
            else:
                # Comportamiento original para otros servicios/hojas
                for col_idx, fecha in enumerate(fechas_unicas):
                    val = row[fecha]
                    if pd.isna(val) or str(val).lower() == 'nan': val = ""
                    val = str(val)
                    is_sep = self._es_fin_de_semana_sep(fecha)
                    
                    fmt = self.styles.cell_week if is_sep else self.styles.cell
                    if renombrar_francos and val in ["F", "FLR"]:
                        val = "FS"
                        fmt = self.styles.grey_cell_week if is_sep else self.styles.grey_cell
                    elif val in ["F", "FS", "LAR", "LPP", "LM", "CM"]:
                        fmt = self.styles.grey_cell_week if is_sep else self.styles.grey_cell
                    elif val == "FLR":
                        fmt = self.styles.dark_grey_cell_week if is_sep else self.styles.dark_grey_cell
                    
                    # Si es servicio 3 (médicos) y tenemos registradas las celdas del cronograma
                    if self.servicio_id == 3 and self.cronograma_celdas:
                        apellido = solo_apellido(nombre)
                        celdas_dia = self.cronograma_celdas.get(fecha, [])
                        if celdas_dia:
                            val_defecto = val if val in ["LAR", "LPP", "LM", "CM"] else "F"
                            
                            formula_parts = []
                            for t_exacto, ref_celda in celdas_dia:
                                abr_turno = get_abreviacion(t_exacto)
                                formula_parts.append(f"IF({ref_celda}=\"{apellido}\",\"{abr_turno}\",")
                            
                            formula_str = "=" + "".join(formula_parts) + f"\"{val_defecto}\"" + (")" * len(formula_parts))
                            
                            ws.write_formula(row_ex, col_idx + 1, formula_str, self.styles.cell_week if is_sep else self.styles.cell, value=val)
                        else:
                            ws.write(row_ex, col_idx + 1, val, fmt)
                    else:
                        ws.write(row_ex, col_idx + 1, val, fmt)
            
            # Escribir columnas de extensión si existen
            if extension_columns:
                for i_ext, col_name in enumerate(extension_columns):
                    col_idx_excel = col_offset + i_ext
                    val_to_write = row[col_name]
                    
                    if formulas and col_name in formulas:
                        fmt_vars = {
                            'row': row_ex + 1,
                            'end_col': end_col_letter,
                        }
                        # Agregar letras de las otras columnas de extensión
                        for other_col in extension_columns:
                            other_idx = col_offset + extension_columns.index(other_col)
                            fmt_vars[other_col.replace(".", "").replace(" ", "_")] = col_to_letter(other_idx)
                        
                        template = formulas[col_name]
                        formula_str = template.format(**fmt_vars)
                        ws.write_formula(row_ex, col_idx_excel, formula_str, self.styles.cell)
                    else:
                        ws.write(row_ex, col_idx_excel, val_to_write, self.styles.cell)
            row_ex += 1
            
        # Formato condicional dinámico para celdas grises (Francos y Licencias) en médicos (servicio 3)
        if self.servicio_id == 3:
            for col_idx, fecha in enumerate(fechas_unicas):
                col_let = col_to_letter(col_idx + 1)
                rango_col = f"{col_let}3:{col_let}{row_ex}"
                is_sep = self._es_fin_de_semana_sep(fecha)
                fmt_condicional = self.styles.grey_cell_week if is_sep else self.styles.grey_cell
                
                for estado_gris in ["F", "LAR", "LPP", "LM", "CM"]:
                    ws.conditional_format(rango_col, {
                        'type': 'cell',
                        'criteria': 'equal to',
                        'value': f'"{estado_gris}"',
                        'format': fmt_condicional
                    })
            
        return ws, row_ex

    def generar_reporte_resumen_sheet(self, df_reporte, sheet_name='Reporte de Horas'):
        ws = self.workbook.add_worksheet(sheet_name)
        ws.freeze_panes(1, 1)

        # Cabeceras
        for col_idx, col_name in enumerate(df_reporte.columns):
            ws.write(0, col_idx, col_name, self.styles.header_blue)
            ws.set_column(col_idx, col_idx, 15)
        ws.set_column(0, 0, 30) # Columna de Nombre más ancha

        # Datos
        for row_idx, row_data in enumerate(df_reporte.values):
            row_num = row_idx + 1
            for col_idx, val in enumerate(row_data):
                fmt = self.styles.cell
                if col_idx == 0: fmt = self.styles.name_cell
                
                # Formato especial para porcentajes si el valor es string con %
                if isinstance(val, str) and val.endswith('%'):
                    ws.write(row_num, col_idx, val, fmt)
                else:
                    ws.write(row_num, col_idx, val, fmt)
        
        return ws

    def close(self):
        import time
        retries = 0
        while True:
            try:
                self.writer.close()
                print(f"Excel generado con exito! Archivo: {self.file_name}")
                break
            except PermissionError:
                retries += 1
                if retries > 5:
                    print("[ERROR] No se pudo guardar el archivo porque sigue abierto.")
                    break
                print(f"\n[ERROR] No se puede guardar '{self.file_name}'.")
                print("   El archivo esta siendo usado por otra aplicacion.")
                print(f"   Por favor, cerralo. Reintentando en 3 segundos... (Intento {retries}/5)")
                time.sleep(3)
            except Exception as e:
                print(f"[ERROR] Error inesperado al guardar el archivo: {e}")
                break
