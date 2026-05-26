import sqlite3
import pandas as pd
import sys
import datetime
from datetime import date, timedelta
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas
import data

# VARIABLE CONFIGURABLE DE ID DE CRONOGRAMA
# Dejar en None para autoseleccionar/preguntar en consola.
# Cambiar por un número entero (ej: 191) para forzar la exportación de un cronograma específico.
CRONOGRAMA_ID_FORZADO = 197

# Cargar Feriados de data.py
FERIADOS = getattr(data, 'FERIADOS', [])

# Mapeo de meses a español
MESES = {
    1: "ENERO", 2: "FEBRERO", 3: "MARZO", 4: "ABRIL", 5: "MAYO", 6: "JUNIO",
    7: "JULIO", 8: "AGOSTO", 9: "SEPTIEMBRE", 10: "OCTUBRE", 11: "NOVIEMBRE", 12: "DICIEMBRE"
}

MAPEO_NOMBRES = {
    "Aguilera Graciela": "Aguilera",
    "Arias Guillermina": "Arias",
    "Baracat Denisse": "Baracat",
    "Barloa Matas Damin": "Barloa",
    "Barloa Matías Damián": "Barloa",
    "Diaz Villafae Morales Abigail": "Diaz",
    "Diaz Villafañe Morales Abigail": "Diaz",
    "Garcia Rodriguez, Maria Eugenia.": "Garcia R.",
    "Godoy Maria": "Godoy",
    "Kolarik Jorge Luis": "Kolarik",
    "Silva, Martn Enrique": "Silva",
    "Silva, Martín Enrique": "Silva",
    "Mora, Sergio Enrique": "Mora",
    "Motta, Mayra Belen": "Motta",
    "Moya, Pedro": "Moya",
    "Murillo, Santiago": "Murillo",
    "Navarro Suarez Gabriela Beln": "Suarez",
    "Navarro Suarez Gabriela Belén": "Suarez",
    "Nesteruk Mara Silvia": "Nesteruk",
    "Nesteruk María Silvia": "Nesteruk",
    "Noriega Claudio Martn": "Noriega",
    "Noriega Claudio Martín": "Noriega",
    "Pregot Analia Mariana": "Pregot",
    "Quintero Anabela Belen": "Quintero",
    "Quiroga Sassu Maria Macarena": "Quiroga",
    "Snchez Reinoso Ana Beln": "Sánchez",
    "Sánchez Reinoso Ana Belén": "Sánchez",
    "Zeballos Valeria Alejandra": "Zeballos",
    "Arce Carolina": "Arce",
    "Pacheco Celeste": "Pacheco",
    "Biscarra Joaqun Martin": "Biscarra",
    "Biscarra Joaquín Martin": "Biscarra",
    "Villegas Oliva Maria Beln": "Villegas",
    "Villegas Oliva Maria Belén": "Villegas",
    "Matricadi Wendy Ailen": "Matricadi",
    "Nez Florencia Natalia": "Núñez",
    "Núñez Florencia Natalia": "Núñez",
    "Palermo Agustn": "Palermo",
    "Palermo Agustín": "Palermo"
}

def simplificar_nombre(nombre):
    if not nombre:
        return ""
    if nombre in MAPEO_NOMBRES:
        return MAPEO_NOMBRES[nombre]
    
    # Limpieza alternativa de caracteres rotos
    nombre_limpio = nombre.replace('\ufffd', '')
    for k, v in MAPEO_NOMBRES.items():
        if k.replace('\ufffd', '') == nombre_limpio:
            return v
            
    if "," in nombre:
        return nombre.split(",")[0].strip()
    partes = nombre.split()
    if partes:
        return partes[0]
    return nombre

# Canvas personalizado de dos pasadas para calcular y mostrar el pie de página
class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []
        self.crono_id = None

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            super().showPage()
        super().save()

    def draw_page_number(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor('#888888'))
        
        # Dibujar una línea divisoria arriba del pie de página
        self.setStrokeColor(colors.HexColor('#CCCCCC'))
        self.setLineWidth(0.5)
        self.line(30, 40, 841.89 - 30, 40)
        
        # Texto del número de página (derecha)
        page_text = f"Página {self._pageNumber} de {page_count}"
        self.drawRightString(841.89 - 30, 25, page_text)
        
        # Timestamp de generación (izquierda)
        fecha_gen = datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        id_text = f" | ID Cronograma: {self.crono_id}" if self.crono_id is not None else ""
        created_text = f"Generado el {fecha_gen}{id_text} | Cronograma UTI Área Médica"
        self.drawString(30, 25, created_text)
        
        self.restoreState()

def select_cronograma_id():
    conn = sqlite3.connect('cronograma_inteligente.db')
    cursor = conn.cursor()
    # Buscar cronogramas recientes que tengan asignaciones médicas
    query = """
        SELECT DISTINCT c.id, c.fecha_inicio, c.fecha_fin, c.creado_en, c.notas
        FROM cronogramas c
        JOIN guardias g ON c.id = g.cronograma_id
        JOIN personal p ON g.nombre = p.nombre
        WHERE p.servicio_id = 3
        ORDER BY c.id DESC
        LIMIT 10
    """
    try:
        rows = cursor.execute(query).fetchall()
    except sqlite3.OperationalError:
        query = "SELECT id, fecha_inicio, fecha_fin, creado_en, notas FROM cronogramas ORDER BY id DESC LIMIT 10"
        rows = cursor.execute(query).fetchall()
    conn.close()
    
    if not rows:
        print("No se encontraron cronogramas en la base de datos.")
        return None
        
    print("\n=== SELECCIONE EL CRONOGRAMA A EXPORTAR A PDF ===")
    for idx, row in enumerate(rows):
        c_id, f_ini, f_fin, creado, notas = row
        creado_f = creado.split("T")[0] if creado else "N/A"
        notas_f = f" - ({notas})" if notas else ""
        print(f"  {idx + 1}: ID {c_id} | Período: {f_ini} al {f_fin} | Creado: {creado_f}{notas_f}")
        
    try:
        opcion = input(f"\nSeleccione una opción (1-{len(rows)}) o presione ENTER para el último [1]: ").strip()
        if opcion == "":
            return rows[0][0]
        val = int(opcion)
        if 1 <= val <= len(rows):
            return rows[val - 1][0]
        else:
            print("Opción inválida. Cancelando.")
            return None
    except (ValueError, KeyboardInterrupt):
        print("\nOperación cancelada.")
        return None

def obtener_datos_cronograma(crono_id):
    conn = sqlite3.connect('cronograma_inteligente.db')
    cursor = conn.cursor()
    
    # Validar existencia del cronograma
    crono = cursor.execute("SELECT fecha_inicio, fecha_fin, notas FROM cronogramas WHERE id = ?", (crono_id,)).fetchone()
    if not crono:
        print(f"ERROR: No se encontró el Cronograma ID {crono_id} en la base de datos.")
        conn.close()
        return None
        
    fecha_inicio, fecha_fin, notas = crono
    
    # Cargar guardias médicas (Servicio 3)
    query = """
        SELECT g.fecha, g.turno, g.nombre
        FROM guardias g
        JOIN personal p ON g.nombre = p.nombre
        WHERE g.cronograma_id = ? AND p.servicio_id = 3
        ORDER BY g.fecha, g.turno, g.nombre
    """
    rows = cursor.execute(query, (crono_id,)).fetchall()
    conn.close()
    
    return {
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin,
        "notas": notas,
        "guardias": rows
    }

def procesar_guardias(rows):
    guardias_por_fecha = {}
    for fecha, turno, nombre in rows:
        guardias_por_fecha.setdefault(fecha, { "Guardia": [], "Día": [], "Noche": [] })
        
        # Mapear turno a categorías simplificadas
        t_upper = turno.upper()
        if t_upper.startswith('G'):
            guardias_por_fecha[fecha]["Guardia"].append(nombre)
        elif t_upper.startswith('D'):
            guardias_por_fecha[fecha]["Día"].append(nombre)
        elif t_upper.startswith('N'):
            guardias_por_fecha[fecha]["Noche"].append(nombre)
        else:
            # Fallback seguro
            guardias_por_fecha[fecha]["Guardia"].append(nombre)
            
    return guardias_por_fecha

def construir_semanas(fecha_inicio_str, fecha_fin_str):
    fecha_inicio = datetime.datetime.strptime(fecha_inicio_str, "%Y-%m-%d").date()
    fecha_fin = datetime.datetime.strptime(fecha_fin_str, "%Y-%m-%d").date()
    
    # Lunes de la primera semana del grid
    lunes_inicio = fecha_inicio - timedelta(days=fecha_inicio.weekday())
    # Domingo de la última semana del grid
    domingo_fin = fecha_fin + timedelta(days=6 - fecha_fin.weekday())
    
    semanas = []
    current_day = lunes_inicio
    week = []
    
    while current_day <= domingo_fin:
        date_str = current_day.isoformat()
        in_range = (fecha_inicio <= current_day <= fecha_fin)
        is_weekend = (current_day.weekday() >= 5)
        is_holiday = (date_str in FERIADOS)
        
        day_info = {
            "date": current_day,
            "date_str": date_str,
            "day_num": str(current_day.day) if in_range else "",
            "in_range": in_range,
            "is_shaded": in_range and (is_weekend or is_holiday)
        }
        week.append(day_info)
        
        if len(week) == 7:
            semanas.append(week)
            week = []
            
        current_day += timedelta(days=1)
        
    return semanas

def build_cell_paragraph(day_info, data_dia, style_cell_text, style_day_num):
    if not day_info["in_range"]:
        return Paragraph("", style_cell_text)
        
    day_num = day_info["day_num"]
    
    # Recolectar todas las líneas de contenido
    lines_content = []
    
    if data_dia:
        if data_dia.get("Guardia"):
            for n in data_dia["Guardia"]:
                lines_content.append(f"- {simplificar_nombre(n)}")
                
        if data_dia.get("Día"):
            lines_content.append("<b>Día (8-20):</b>")
            for n in data_dia["Día"]:
                lines_content.append(f"- {simplificar_nombre(n)}")
                
        if data_dia.get("Noche"):
            lines_content.append("<b>Noche (20-8):</b>")
            for n in data_dia["Noche"]:
                lines_content.append(f"- {simplificar_nombre(n)}")

    first_line = lines_content[0] if lines_content else ""
    remaining_lines = lines_content[1:] if len(lines_content) > 1 else []
    
    # Sub-tabla para alinear a la izquierda la primera línea/nombre y a la derecha el número de día
    p_left = Paragraph(first_line, style_cell_text)
    p_right = Paragraph(f"<b>{day_num}</b>", style_day_num)
    
    sub_table_style = TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ])
    
    # Ancho total disponible en la celda: col_width - 6 padding = ~105
    sub_table = Table([[p_left, p_right]], colWidths=[87, 18])
    sub_table.setStyle(sub_table_style)
    
    if remaining_lines:
        p_remaining = Paragraph("<br/>".join(remaining_lines), style_cell_text)
        return [sub_table, p_remaining]
    else:
        return sub_table

def format_cell_p2(val, style_text):
    val_str = str(val) if val is not None else ""
    
    # Simplificar a D, G, N, F o Licencia
    if val_str.startswith("D"):
        display_val = "D"
    elif val_str.startswith("G"):
        display_val = "G"
    elif val_str.startswith("N"):
        display_val = "N"
    else:
        display_val = val_str
        
    if display_val == "F":
        return Paragraph("<font color='#666666'>F</font>", style_text)
    elif display_val in ["LAR", "LPP", "LM", "CM"]:
        return Paragraph(f"<font color='#C0392B'><b>{display_val}</b></font>", style_text)
    elif display_val in ["D", "G", "N"]:
        return Paragraph(f"<b>{display_val}</b>", style_text)
    else:
        return Paragraph(display_val, style_text)

def generar_pdf(crono_id, fecha_inicio, fecha_fin, notas, guardias_por_fecha, semanas, df_resultados, df_personal, flrs_asignados, output_filename):
    # A4 horizontal tiene 841.89 ptos de ancho y 595.27 ptos de alto
    doc = SimpleDocTemplate(
        output_filename,
        pagesize=landscape(A4),
        leftMargin=30,
        rightMargin=30,
        topMargin=20,
        bottomMargin=50
    )
    
    story = []
    
    fecha_dt = datetime.datetime.strptime(fecha_inicio, "%Y-%m-%d")
    mes_str = MESES[fecha_dt.month]
    anio = fecha_dt.year
    
    title_text = "CRONOGRAMA DE GUARDIAS - ÁREA MÉDICA UTI"
    subtitle_text = f"PERÍODO: {mes_str} {anio}"
    if notas and notas != "Generado via CLI":
        subtitle_text += f" ({notas})"
        
    style_title = ParagraphStyle(
        name='TitleStyle',
        fontName='Helvetica-Bold',
        fontSize=15,
        textColor=colors.HexColor('#1C3144'),
        alignment=1,
        spaceAfter=3
    )
    
    style_subtitle = ParagraphStyle(
        name='SubtitleStyle',
        fontName='Helvetica-Bold',
        fontSize=10,
        textColor=colors.HexColor('#555555'),
        alignment=1,
        spaceAfter=8
    )
    
    story.append(Paragraph(title_text, style_title))
    story.append(Paragraph(subtitle_text, style_subtitle))
    
    style_header = ParagraphStyle(
        name='HeaderStyle',
        fontName='Helvetica-Bold',
        fontSize=10,
        textColor=colors.white,
        alignment=1,
        spaceAfter=0
    )

    style_cell_text = ParagraphStyle(
        name='CellTextStyle',
        fontName='Helvetica',
        fontSize=8.0,
        leading=7.5,
        textColor=colors.HexColor('#1A1A1A'),
        alignment=0,
        spaceAfter=0
    )
    
    style_day_num = ParagraphStyle(
        name='DayNumStyle',
        fontName='Helvetica-Bold',
        fontSize=8.0,
        leading=8.0,
        textColor=colors.HexColor('#1C3144'),
        alignment=2,
        spaceAfter=0
    )
    
    headers = ['LUNES', 'MARTES', 'MIÉRCOLES', 'JUEVES', 'VIERNES', 'SÁBADO', 'DOMINGO']
    table_data = []
    
    # Fila 0: Encabezados de días de la semana
    table_data.append([Paragraph(h, style_header) for h in headers])
    
    t_styles = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1C3144')),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#999999')),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('LEFTPADDING', (0, 0), (-1, -1), 3),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3),
    ]
    
    # Rellenar filas de semanas y marcar sombreado
    for r_idx, week in enumerate(semanas):
        row = []
        for c_idx, day_info in enumerate(week):
            data_dia = guardias_por_fecha.get(day_info["date_str"], {})
            cell_p = build_cell_paragraph(day_info, data_dia, style_cell_text, style_day_num)
            row.append(cell_p)
            
            table_row = r_idx + 1
            if day_info["is_shaded"]:
                t_styles.append(('BACKGROUND', (c_idx, table_row), (c_idx, table_row), colors.HexColor('#E8E8E8')))
                
        table_data.append(row)
        
    # Calcular tamaños y distribuir celdas para que quepa exactamente en 1 página
    available_height = 475
    header_height = 22
    num_weeks = len(semanas)
    row_height = (available_height - header_height) / num_weeks
    
    col_widths = [781.89 / 7] * 7
    row_heights = [header_height] + [row_height] * num_weeks
    
    table = Table(table_data, colWidths=col_widths, rowHeights=row_heights)
    table.setStyle(TableStyle(t_styles))
    story.append(table)
    
    # --- PÁGINA 2: VISTA POR PERSONAL ---
    story.append(PageBreak())
    
    story.append(Paragraph(title_text, style_title))
    story.append(Paragraph(f"RESUMEN INDIVIDUAL POR PERSONAL - {mes_str} {anio}", style_subtitle))
    
    from reportes.medicos import exportar_excel_vista_personal
    df_persona = exportar_excel_vista_personal(df_resultados, df_personal, flrs_asignados)
    
    fechas_unicas = sorted(df_resultados['Fecha'].unique().tolist())
    p2_headers = ['PERSONAL'] + [f.split('-')[-1] for f in fechas_unicas]
    
    p2_table_data = []
    p2_table_data.append([Paragraph(f"<b>{h}</b>", style_header) for h in p2_headers])
    
    p2_styles = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1C3144')),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CCCCCC')),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('LEFTPADDING', (0, 0), (-1, -1), 2),
        ('RIGHTPADDING', (0, 0), (-1, -1), 2),
    ]
    
    style_cell_p2 = ParagraphStyle(
        name='CellTextStyleP2',
        fontName='Helvetica',
        fontSize=6.5,
        leading=8,
        textColor=colors.HexColor('#1A1A1A'),
        alignment=1,
        spaceAfter=0
    )

    style_cell_name = ParagraphStyle(
        name='CellNameStyle',
        fontName='Helvetica-Bold',
        fontSize=7.5,
        leading=9,
        textColor=colors.HexColor('#1C3144'),
        alignment=0,
        spaceAfter=0
    )
    
    nombres_ordenados = sorted(df_persona.index.tolist(), key=simplificar_nombre)
    for r_idx, nombre in enumerate(nombres_ordenados):
        table_row = r_idx + 1
        nombre_simplificado = simplificar_nombre(nombre)
        row = [Paragraph(nombre_simplificado, style_cell_name)]
        
        for f in fechas_unicas:
            val = df_persona.at[nombre, f]
            row.append(format_cell_p2(val, style_cell_p2))
            
        bg_color = colors.HexColor('#FFFFFF') if r_idx % 2 == 0 else colors.HexColor('#F5F7FA')
        p2_styles.append(('BACKGROUND', (0, table_row), (-1, table_row), bg_color))
        
        p2_table_data.append(row)
        
    num_days = len(fechas_unicas)
    col_w_name = 80
    col_w_day = 22
    col_widths_p2 = [col_w_name] + [col_w_day] * num_days
    
    row_height_p2 = 14
    row_heights_p2 = [18] + [row_height_p2] * len(nombres_ordenados)
    
    table_p2 = Table(p2_table_data, colWidths=col_widths_p2, rowHeights=row_heights_p2)
    table_p2.setStyle(TableStyle(p2_styles))
    story.append(table_p2)
    
    story.append(Spacer(1, 10))
    style_legend = ParagraphStyle(
        name='LegendStyle',
        fontName='Helvetica',
        fontSize=6.5,
        leading=8,
        textColor=colors.HexColor('#555555'),
        alignment=0,
        spaceAfter=0
    )
    
    legend_html = (
        "<b>REFERENCIAS DE TURNOS:</b> D: Día (8-20) | N: Noche (20-8) | G: Guardia (24h) | F: Franco | "
        "LAR / LPP / LM / CM: Licencias."
    )
    story.append(Paragraph(legend_html, style_legend))
    
    class CustomNumberedCanvas(NumberedCanvas):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.crono_id = crono_id
            
    doc.build(story, canvasmaker=CustomNumberedCanvas)

def obtener_estructuras_reporte(crono_id, fecha_inicio, fecha_fin):
    conn = sqlite3.connect('cronograma_inteligente.db')
    cursor = conn.cursor()
    
    # 1. df_resultados
    df_resultados = pd.read_sql_query("""
        SELECT fecha as Fecha, nombre as Personal, turno as Turno
        FROM guardias
        WHERE cronograma_id = ?
    """, conn, params=(crono_id,))
    
    # 2. df_personal
    from database.data_loader import obtener_empleados
    fecha_inicio_dt = datetime.datetime.strptime(fecha_inicio, "%Y-%m-%d")
    fecha_fin_dt = datetime.datetime.strptime(fecha_fin, "%Y-%m-%d")
    total_dias = (fecha_fin_dt - fecha_inicio_dt).days + 1
    
    empleados = obtener_empleados(3, fecha_inicio, total_dias)
    df_personal = pd.DataFrame([vars(e) for e in empleados])
    df_personal = df_personal.rename(columns={'nombre': 'Nombre', 'rol': 'Rol'})
    
    # 3. flrs_asignados
    cursor.execute("""
        SELECT nombre, fecha_inicio, fecha_fin
        FROM flr_asignados
        WHERE cronograma_id = ?
    """, (crono_id,))
    flrs_rows = cursor.fetchall()
    flrs_asignados = [{'nombre': r[0], 'fecha_inicio': r[1], 'fecha_fin': r[2]} for r in flrs_rows]
    
    conn.close()
    return df_resultados, df_personal, flrs_asignados

def main():
    if CRONOGRAMA_ID_FORZADO is not None:
        crono_id = CRONOGRAMA_ID_FORZADO
    elif len(sys.argv) > 1:
        try:
            crono_id = int(sys.argv[1])
        except ValueError:
            print("ERROR: El ID del cronograma debe ser un número entero.")
            return
    else:
        crono_id = select_cronograma_id()
        if crono_id is None:
            return
            
    print(f"\nProcesando Cronograma ID: {crono_id}...")
    datos = obtener_datos_cronograma(crono_id)
    if not datos:
        return
        
    fecha_inicio = datos["fecha_inicio"]
    fecha_fin = datos["fecha_fin"]
    notas = datos["notas"]
    guardias_rows = datos["guardias"]
    
    if not guardias_rows:
        print(f"\nADVERTENCIA: No se encontraron asignaciones del Área Médica (Servicio 3) para el Cronograma ID {crono_id}.")
        print("¿Desea exportar el PDF de todos modos? Se generará el calendario vacío.")
        try:
            cont = input("¿Continuar? (s/n): ").strip().lower()
            if cont != 's':
                print("Operación cancelada.")
                return
        except (KeyboardInterrupt, ValueError):
            return
            
    print(f"[OK] Cargadas {len(guardias_rows)} asignaciones de guardia.")
    print(f"     Período: {fecha_inicio} al {fecha_fin}")
    
    # Procesar datos
    guardias_por_fecha = procesar_guardias(guardias_rows)
    semanas = construir_semanas(fecha_inicio, fecha_fin)
    
    # Cargar licencias e inicializar dicts de queries para el reporte
    from database import queries as db_queries
    db_queries.init_licencias()
    
    df_resultados, df_personal, flrs_asignados = obtener_estructuras_reporte(crono_id, fecha_inicio, fecha_fin)
    
    # Nombre del archivo final
    fecha_dt = datetime.datetime.strptime(fecha_inicio, "%Y-%m-%d")
    mes_str = MESES[fecha_dt.month].capitalize()
    anio = fecha_dt.year
    output_filename = f"Cronograma_Medicos_{mes_str}_{anio}.pdf"
    
    print(f"Generando PDF: {output_filename}...")
    try:
        generar_pdf(crono_id, fecha_inicio, fecha_fin, notas, guardias_por_fecha, semanas, df_resultados, df_personal, flrs_asignados, output_filename)
        print(f"\n[SUCCESS] PDF generado con éxito: {output_filename}!")
    except Exception as e:
        print(f"\n[ERROR] Ocurrió un error al generar el PDF: {e}")

if __name__ == '__main__':
    main()
