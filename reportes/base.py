import pandas as pd
from datetime import date, timedelta
from database import queries as database

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
        return 12
    if "24" in turno and "-" not in turno:
        return 12
    return 6

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
            'FSL4': int(_safe_float(p.get('findes_largos_4_previos'), 0.0) + fsl4_act.get(nombre, 0))
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
    def __init__(self, file_name, feriados=None, fecha_inicio=None, crono_id=None):
        self.file_name = file_name
        self.crono_id = crono_id
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

    def escribir_cabeceras_calendario(self, ws, fechas_unicas, start_col=1, col_width=12):
        """Escribe las dos filas de cabecera (Día Sigla y Fecha)."""
        for col_idx, fecha in enumerate(fechas_unicas):
            dt = date.fromisoformat(fecha)
            sigla = self.siglas_dias[dt.weekday()]
            dia_num = f"{dt.day}/{dt.month}"
            
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

            ws.write(0, start_col + col_idx, sigla, fmt_h1)
            ws.write(1, start_col + col_idx, dia_num, fmt_h2)
            ws.set_column(start_col + col_idx, start_col + col_idx, col_width)

    def generar_cronograma_sheet(self, df_pivot, fechas_unicas, sheet_name='Cronograma'):
        ws = self.workbook.add_worksheet(sheet_name)
        ws.freeze_panes(2, 1) # Inmovilizar 2 filas y 1 columna
        
        # Cabecera Lateral
        ws.merge_range(0, 0, 1, 0, "TURNO", self.styles.header_blue)
        ws.set_column(0, 0, 15)
        
        # Cabeceras de Fecha
        self.escribir_cabeceras_calendario(ws, fechas_unicas)
        
        # Datos
        row_ex = 2
        for turno_label, row in df_pivot.iterrows():
            ws.write(row_ex, 0, turno_label, self.styles.header_blue)
            for col_idx, fecha in enumerate(fechas_unicas):
                val = row[fecha]
                if pd.isna(val) or str(val).lower() == 'nan': val = ""
                val = str(val)
                is_sep = self._es_fin_de_semana_sep(fecha)
                
                # Formato según valor
                if turno_label in ["LPP", "LAR", "LM", "CM"]:
                    fmt = self.styles.grey_cell_week if is_sep else self.styles.grey_cell
                else:
                    # Intentar obtener color de turno
                    base_turno = turno_label.split('_')[0]
                    fmt = self.styles.get_shift_format(base_turno, is_sep)
                
                ws.write(row_ex, col_idx + 1, val, fmt)
            
            # Ajustar altura
            if turno_label in ["LPP", "LAR", "LM", "CM"]:
                ws.set_row(row_ex, 30)
            elif str(turno_label).strip() == "":
                ws.set_row(row_ex, 15)
            row_ex += 1
        return ws

    def generar_vista_personal_sheet(self, df_persona, fechas_unicas, extension_columns=None, label_personal="PERSONAL", sheet_name='Vista por Personal'):
        ws = self.workbook.add_worksheet(sheet_name)
        ws.freeze_panes(2, 1) # Inmovilizar 2 filas y 1 columna

        # Cabecera Lateral
        ws.merge_range(0, 0, 1, 0, label_personal, self.styles.header_blue)
        ws.set_column(0, 0, 25)
        
        # Cabeceras de Fecha (más angostas aquí)
        self.escribir_cabeceras_calendario(ws, fechas_unicas, col_width=6)
        
        col_offset = len(fechas_unicas) + 2 # +1 por nombre, +1 por columna en blanco
        
        # Columna en blanco de separación
        ws.set_column(col_offset - 1, col_offset - 1, 2) 

        # Columnas de Extensión (Totales, etc)
        if extension_columns:
            for i, col_name in enumerate(extension_columns):
                ws.merge_range(0, col_offset + i, 1, col_offset + i, col_name, self.styles.header_blue)
                ws.set_column(col_offset + i, col_offset + i, 10)

        # Datos de Personal
        row_ex = 2
        for nombre, row in df_persona.iterrows():
            ws.write(row_ex, 0, nombre, self.styles.name_cell)
            for col_idx, fecha in enumerate(fechas_unicas):
                val = row[fecha]
                if pd.isna(val) or str(val).lower() == 'nan': val = ""
                val = str(val)
                is_sep = self._es_fin_de_semana_sep(fecha)
                
                fmt = self.styles.cell_week if is_sep else self.styles.cell
                if val in ["F", "LAR", "LPP", "LM", "CM"]:
                    fmt = self.styles.grey_cell_week if is_sep else self.styles.grey_cell
                elif val == "FLR":
                    fmt = self.styles.dark_grey_cell_week if is_sep else self.styles.dark_grey_cell
                
                ws.write(row_ex, col_idx + 1, val, fmt)
            
            # Escribir columnas de extensión
            if extension_columns:
                for i, col_name in enumerate(extension_columns):
                    ws.write(row_ex, col_offset + i, row[col_name], self.styles.cell)
            row_ex += 1
            
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
