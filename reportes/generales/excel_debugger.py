from database import queries as db_queries

def inyectar_reporte_infracciones(report, crono_id):
    """
    Consulta las infracciones desde la DB para crono_id e inyecta la primera hoja
    'Infracciones (DEBUG)' en el workbook de report (BaseReport).
    """
    infracciones = db_queries.obtener_infracciones(crono_id)
    if not infracciones:
        return

    # Crear la hoja
    ws = report.workbook.add_worksheet("Infracciones (DEBUG)")
    ws.activate()

    # Formato premium para cabecera de alerta
    header_alert = report.workbook.add_format({
        'bold': True,
        'bg_color': '#FCE4D6',   # Salmón/Naranja suave de alerta
        'font_color': '#C00000', # Texto rojo oscuro
        'border': 2,
        'align': 'center',
        'valign': 'vcenter',
        'font_size': 13,
        'font_name': 'Calibri'
    })

    # Cabeceras de la tabla
    header_table = report.workbook.add_format({
        'bold': True,
        'bg_color': '#4F81BD',   # Azul corporativo premium
        'font_color': '#FFFFFF', # Texto blanco
        'border': 1,
        'align': 'center',
        'valign': 'vcenter',
        'font_size': 10,
        'font_name': 'Calibri'
    })

    # Celdas estándar y de etiquetas
    cell_format = report.workbook.add_format({
        'border': 1,
        'align': 'left',
        'valign': 'vcenter',
        'font_size': 9,
        'font_name': 'Calibri',
        'text_wrap': True
    })

    rule_name_format = report.workbook.add_format({
        'bold': True,
        'border': 1,
        'align': 'center',
        'valign': 'vcenter',
        'bg_color': '#F2F2F2',
        'font_size': 9,
        'font_name': 'Calibri'
    })

    # Escribir título
    ws.merge_range(0, 0, 0, 2, "REPORTE DE INFRACCIONES - MODO DIAGNÓSTICO", header_alert)
    ws.set_row(0, 32)

    # Escribir cabeceras de columnas
    ws.write(2, 0, "REGLA COMPROMETIDA", header_table)
    ws.write(2, 1, "DESCRIPCIÓN DE LA REGLA", header_table)
    ws.write(2, 2, "DETALLE DE LA INFRACCIÓN (EMPLEADO / DÍA)", header_table)
    ws.set_row(2, 24)

    # Configurar anchos
    ws.set_column(0, 0, 28) # Regla
    ws.set_column(1, 1, 55) # Descripción
    ws.set_column(2, 2, 45) # Detalle

    row_idx = 3
    for codigo_regla, descripcion, detalle in infracciones:
        ws.write(row_idx, 0, codigo_regla, rule_name_format)
        ws.write(row_idx, 1, descripcion, cell_format)
        ws.write(row_idx, 2, detalle, cell_format)
        ws.set_row(row_idx, 22)
        row_idx += 1

    # Agregar una línea vacía y un mensaje al final
    row_idx += 1
    info_format = report.workbook.add_format({
        'italic': True,
        'font_size': 9,
        'font_color': '#595959',
        'font_name': 'Calibri'
    })
    ws.merge_range(row_idx, 0, row_idx, 2, "* Nota: Este cronograma fue forzado en MODO_DEBUG para permitir el diagnóstico visual de las reglas sacrificadas.", info_format)
