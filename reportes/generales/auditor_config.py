"""
Inspector/Auditor de configuraciones del motor de cronogramas.
Extrae a Excel y Markdown el estado completo de reglas, perfiles, demandas y ajustes
que aplican a un servicio_id y mes/año específicos.
Uso: python auditor_config.py --fecha YYYY-MM --servicio_id ID
"""

import os
import sys
import json
import argparse
import calendar
import sqlite3
import pandas as pd
from datetime import datetime

# Asegurar que la raíz del proyecto está en el path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from database.connection import get_connection

def parse_args():
    parser = argparse.ArgumentParser(description="Auditor de Configuraciones de Cronogramas")
    parser.add_argument("--fecha", type=str, default="2026-06", help="Mes a auditar en formato YYYY-MM (ej. 2026-06)")
    parser.add_argument("--servicio_id", type=int, default=1, help="ID del servicio a auditar (ej. 1)")
    parser.add_argument("--db", type=str, default=None, help="Ruta alternativa de la base de datos SQLite")
    return parser.parse_args()

def obtener_rango_mes(fecha_str):
    try:
        parts = fecha_str.split("-")
        year = int(parts[0])
        month = int(parts[1])
    except Exception:
        today = datetime.today()
        year = today.year
        month = today.month
        print(f"[WARN] Formato de fecha inválido. Usando mes actual: {year:04d}-{month:02d}")
    
    last_day = calendar.monthrange(year, month)[1]
    fecha_inicio = f"{year:04d}-{month:02d}-01"
    fecha_fin = f"{year:04d}-{month:02d}-{last_day:02d}"
    return fecha_inicio, fecha_fin, year, month

def formatear_json(json_str):
    if not json_str:
        return ""
    try:
        parsed = json.loads(json_str)
        return json.dumps(parsed, ensure_ascii=False)
    except Exception:
        return json_str

def cargar_datos_auditoria(conn, servicio_id, fecha_inicio, fecha_fin):
    # 1. Datos del Servicio y Organización
    serv_query = """
        SELECT s.id as servicio_id, s.nombre as servicio_nombre, o.nombre as organizacion_nombre
        FROM servicios s
        JOIN organizaciones o ON s.organizacion_id = o.id
        WHERE s.id = ?
    """
    df_serv = pd.read_sql_query(serv_query, conn, params=[servicio_id])
    if df_serv.empty:
        raise ValueError(f"No se encontró el servicio con ID {servicio_id} en la base de datos.")
    
    # 2. Reglas aplicables al servicio (combinando org y servicio)
    org_id = conn.execute("SELECT organizacion_id FROM servicios WHERE id = ?", (servicio_id,)).fetchone()[0]
    
    reglas_query = """
        SELECT 
            rc.codigo_regla,
            rc.tipo as regla_tipo,
            rc.descripcion as regla_descripcion,
            COALESCE(sr.parametros_json, oorg.parametros_json) as parametros_json,
            CASE 
                WHEN sr.codigo_regla IS NOT NULL THEN 'Servicio'
                ELSE 'Organización'
            END as origen,
            COALESCE(sr.activo, oorg.activo, 1) as activo
        FROM reglas_catalogo rc
        LEFT JOIN organizaciones_reglas oorg ON rc.codigo_regla = oorg.codigo_regla AND oorg.organizacion_id = ?
        LEFT JOIN servicios_reglas sr ON rc.codigo_regla = sr.codigo_regla AND sr.servicio_id = ?
        WHERE (oorg.activo = 1 OR sr.activo = 1)
        ORDER BY rc.tipo DESC, rc.codigo_regla
    """
    df_reglas = pd.read_sql_query(reglas_query, conn, params=[org_id, servicio_id])
    df_reglas['parametros_json'] = df_reglas['parametros_json'].apply(formatear_json)
    
    # 3. Ajustes de Reglas de Servicio
    ajust_serv_query = """
        SELECT codigo_regla, fecha_inicio, fecha_fin, accion, parametros_json, activo
        FROM servicios_reglas_ajustes
        WHERE servicio_id = ? AND activo = 1 AND (fecha_inicio <= ? AND fecha_fin >= ?)
        ORDER BY fecha_inicio, codigo_regla
    """
    df_ajust_serv = pd.read_sql_query(ajust_serv_query, conn, params=[servicio_id, fecha_fin, fecha_inicio])
    df_ajust_serv['parametros_json'] = df_ajust_serv['parametros_json'].apply(formatear_json)

    # 4. Personal, Categorías, Roles y Puestos
    pers_query = """
        SELECT nombre, categoria, rol, regimen_trabajo, horas_mensuales_reglamentarias, fecha_cumpleanos,
               es_madre, es_padre, activo
        FROM personal
        WHERE servicio_id = ? AND activo = 1
        ORDER BY nombre
    """
    df_pers = pd.read_sql_query(pers_query, conn, params=[servicio_id])
    
    puestos_query = """
        SELECT pp.personal_nombre, p.nombre as puesto_nombre
        FROM personal_puestos pp
        JOIN puestos p ON pp.puesto_id = p.id
        WHERE p.servicio_id = ?
    """
    df_puestos = pd.read_sql_query(puestos_query, conn, params=[servicio_id])
    
    # Agrupar puestos por persona
    puestos_dict = {}
    for _, r in df_puestos.iterrows():
        puestos_dict.setdefault(r['personal_nombre'], []).append(r['puesto_nombre'])
        
    df_pers['puestos'] = df_pers['nombre'].apply(lambda n: ", ".join(puestos_dict.get(n, [])))

    # 5. Reglas Individuales de Personal
    pers_reglas_query = """
        SELECT pr.personal_nombre, pr.codigo_regla, rc.tipo as regla_tipo, rc.descripcion as regla_descripcion, 
               pr.parametros_json, pr.activo
        FROM personal_reglas pr
        JOIN personal p ON pr.personal_nombre = p.nombre
        JOIN reglas_catalogo rc ON pr.codigo_regla = rc.codigo_regla
        WHERE p.servicio_id = ? AND pr.activo = 1
        ORDER BY pr.personal_nombre, pr.codigo_regla
    """
    df_pers_reglas = pd.read_sql_query(pers_reglas_query, conn, params=[servicio_id])
    df_pers_reglas['parametros_json'] = df_pers_reglas['parametros_json'].apply(formatear_json)

    # 6. Ajustes de Reglas Personales
    ajust_pers_query = """
        SELECT pra.personal_nombre, pra.codigo_regla, pra.fecha_inicio, pra.fecha_fin, pra.accion, 
               pra.parametros_json, pra.activo
        FROM personal_reglas_ajustes pra
        JOIN personal p ON pra.personal_nombre = p.nombre
        WHERE p.servicio_id = ? AND pra.activo = 1 AND (pra.fecha_inicio <= ? AND pra.fecha_fin >= ?)
        ORDER BY pra.personal_nombre, pra.fecha_inicio
    """
    df_ajust_pers = pd.read_sql_query(ajust_pers_query, conn, params=[servicio_id, fecha_fin, fecha_inicio])
    df_ajust_pers['parametros_json'] = df_ajust_pers['parametros_json'].apply(formatear_json)

    # 7. Licencias Cargadas
    licencias_query = """
        SELECT l.nombre, l.tipo as tipo_licencia, l.fecha_inicio, l.fecha_fin, l.metadata
        FROM licencias l
        JOIN personal p ON l.nombre = p.nombre
        WHERE p.servicio_id = ? AND (l.fecha_inicio <= ? AND l.fecha_fin >= ?)
        ORDER BY l.nombre, l.fecha_inicio
    """
    df_licencias = pd.read_sql_query(licencias_query, conn, params=[servicio_id, fecha_fin, fecha_inicio])

    # 8. Asignaciones Fijas Previas (Guardias de cronogramas aprobados en el mes)
    guardias_query = """
        SELECT g.nombre, g.fecha, g.turno, g.horas, c.id as cronograma_id, c.notas as cronograma_notas
        FROM guardias g
        JOIN cronogramas c ON g.cronograma_id = c.id
        JOIN personal p ON g.nombre = p.nombre
        WHERE p.servicio_id = ? AND (g.fecha BETWEEN ? AND ?) AND c.estado = 'aprobado'
        ORDER BY g.fecha, g.nombre
    """
    df_guardias = pd.read_sql_query(guardias_query, conn, params=[servicio_id, fecha_inicio, fecha_fin])

    # 9. Demanda y Turnos
    demanda_query = """
        SELECT p.nombre as puesto, dc.tipo_dia, dc.hora_inicio, dc.hora_fin, dc.cantidad_min, dc.cantidad_max, dc.dias_semana
        FROM demanda_config dc
        JOIN puestos p ON dc.puesto_id = p.id
        WHERE p.servicio_id = ? AND dc.activo = 1
        ORDER BY p.nombre, dc.tipo_dia, dc.hora_inicio
    """
    df_demanda = pd.read_sql_query(demanda_query, conn, params=[servicio_id])

    demanda_ajust_query = """
        SELECT p.nombre as puesto, dc.tipo_dia, dc.hora_inicio, dc.hora_fin, 
               da.fecha_inicio, da.fecha_fin, da.cantidad_min, da.cantidad_max, da.dias_semana as dias_semana_ajuste
        FROM demanda_ajustes da
        JOIN demanda_config dc ON da.demanda_config_id = dc.id
        JOIN puestos p ON dc.puesto_id = p.id
        WHERE p.servicio_id = ? AND da.activo = 1 AND dc.activo = 1 AND (da.fecha_inicio <= ? AND da.fecha_fin >= ?)
        ORDER BY p.nombre, da.fecha_inicio
    """
    df_demanda_ajust = pd.read_sql_query(demanda_ajust_query, conn, params=[servicio_id, fecha_fin, fecha_inicio])

    turnos_query = """
        SELECT tc.nombre as turno_nombre, tc.hora_inicio, tc.horas, tc.dias_semana, p.nombre as puesto_nombre, tc.orden
        FROM turnos_config tc
        LEFT JOIN puestos p ON tc.puesto_id = p.id
        WHERE tc.servicio_id = ? AND tc.activo = 1
        ORDER BY tc.orden
    """
    df_turnos = pd.read_sql_query(turnos_query, conn, params=[servicio_id])

    turnos_ajust_query = """
        SELECT tc.nombre as turno_nombre, ta.fecha_inicio, ta.fecha_fin, ta.vacantes, ta.dias_semana as dias_semana_ajuste
        FROM turnos_ajustes ta
        JOIN turnos_config tc ON ta.turno_config_id = tc.id
        WHERE tc.servicio_id = ? AND ta.activo = 1 AND tc.activo = 1 AND (ta.fecha_inicio <= ? AND ta.fecha_fin >= ?)
        ORDER BY tc.nombre, ta.fecha_inicio
    """
    df_turnos_ajust = pd.read_sql_query(turnos_ajust_query, conn, params=[servicio_id, fecha_fin, fecha_inicio])

    return {
        "servicio": df_serv,
        "reglas_servicio": df_reglas,
        "ajustes_servicio": df_ajust_serv,
        "personal": df_pers,
        "reglas_personal": df_pers_reglas,
        "ajustes_personal": df_ajust_pers,
        "licencias": df_licencias,
        "guardias_previas": df_guardias,
        "demanda": df_demanda,
        "demanda_ajustes": df_demanda_ajust,
        "turnos": df_turnos,
        "turnos_ajustes": df_turnos_ajust
    }

def clean_val(val):
    if pd.isna(val) or val is None:
        return ""
    if isinstance(val, float):
        if val.is_integer():
            return int(val)
        return val
    return val

def exportar_excel(data, filename, servicio_nombre, fecha_str):
    writer = pd.ExcelWriter(filename, engine='xlsxwriter')
    workbook = writer.book

    # --- DEFINICIÓN DE FORMATOS ---
    header_format = workbook.add_format({
        'bold': True,
        'bg_color': '#1F497D',   # Azul oscuro corporativo
        'font_color': '#FFFFFF', # Texto blanco
        'border': 1,
        'align': 'center',
        'valign': 'vcenter',
        'font_name': 'Calibri',
        'font_size': 11
    })

    title_format = workbook.add_format({
        'bold': True,
        'font_size': 16,
        'font_name': 'Calibri',
        'font_color': '#1F497D'
    })

    subtitle_format = workbook.add_format({
        'italic': True,
        'font_size': 10,
        'font_name': 'Calibri',
        'font_color': '#595959'
    })

    cell_format = workbook.add_format({
        'border': 1,
        'align': 'left',
        'valign': 'vcenter',
        'font_name': 'Calibri',
        'font_size': 10,
        'text_wrap': True
    })

    num_format = workbook.add_format({
        'border': 1,
        'align': 'center',
        'valign': 'vcenter',
        'font_name': 'Calibri',
        'font_size': 10
    })

    # Pestaña 1: Resumen Servicio
    ws1 = workbook.add_worksheet("Resumen Servicio")
    ws1.write(0, 0, f"AUDITORÍA DE CONFIGURACIÓN - SERVICIO: {servicio_nombre.upper()}", title_format)
    ws1.write(1, 0, f"Período: {fecha_str} | Generado el {datetime.now().strftime('%d/%m/%Y %H:%M')}", subtitle_format)
    
    # Escribir información general del servicio
    ws1.write(3, 0, "SERVICIO GENERAL", workbook.add_format({'bold': True, 'font_size': 12, 'font_color': '#1F497D'}))
    df_serv = data["servicio"]
    ws1.write(4, 0, "ID Servicio", header_format)
    ws1.write(4, 1, "Nombre Servicio", header_format)
    ws1.write(4, 2, "Organización", header_format)
    ws1.write(5, 0, clean_val(df_serv.iloc[0]['servicio_id']), num_format)
    ws1.write(5, 1, clean_val(df_serv.iloc[0]['servicio_nombre']), cell_format)
    ws1.write(5, 2, clean_val(df_serv.iloc[0]['organizacion_nombre']), cell_format)

    # Escribir Reglas de Servicio
    ws1.write(7, 0, "REGLAS DE NEGOCIO DEL SERVICIO", workbook.add_format({'bold': True, 'font_size': 12, 'font_color': '#1F497D'}))
    df_reg = data["reglas_servicio"]
    headers_reg = ["Código Regla", "Tipo", "Descripción", "Parámetros JSON", "Origen", "Activo"]
    for col_idx, h in enumerate(headers_reg):
        ws1.write(8, col_idx, h, header_format)
    
    row_idx = 9
    for _, r in df_reg.iterrows():
        ws1.write(row_idx, 0, clean_val(r['codigo_regla']), cell_format)
        ws1.write(row_idx, 1, clean_val(r['regla_tipo']), num_format)
        ws1.write(row_idx, 2, clean_val(r['regla_descripcion']), cell_format)
        ws1.write(row_idx, 3, clean_val(r['parametros_json']), cell_format)
        ws1.write(row_idx, 4, clean_val(r['origen']), num_format)
        ws1.write(row_idx, 5, "Sí" if r['activo'] == 1 else "No", num_format)
        row_idx += 1

    # Escribir Ajustes de Servicio
    row_idx += 1
    ws1.write(row_idx, 0, "AJUSTES TEMPORALES DEL SERVICIO", workbook.add_format({'bold': True, 'font_size': 12, 'font_color': '#1F497D'}))
    row_idx += 1
    df_aj_serv = data["ajustes_servicio"]
    headers_aj_serv = ["Código Regla", "Fecha Inicio", "Fecha Fin", "Acción", "Parámetros JSON", "Activo"]
    for col_idx, h in enumerate(headers_aj_serv):
        ws1.write(row_idx, col_idx, h, header_format)
    
    row_idx += 1
    if df_aj_serv.empty:
        ws1.write(row_idx, 0, "(Sin ajustes temporales para el mes)", subtitle_format)
        row_idx += 1
    else:
        for _, r in df_aj_serv.iterrows():
            ws1.write(row_idx, 0, clean_val(r['codigo_regla']), cell_format)
            ws1.write(row_idx, 1, clean_val(r['fecha_inicio']), num_format)
            ws1.write(row_idx, 2, clean_val(r['fecha_fin']), num_format)
            ws1.write(row_idx, 3, clean_val(r['accion']), num_format)
            ws1.write(row_idx, 4, clean_val(r['parametros_json']), cell_format)
            ws1.write(row_idx, 5, "Sí" if r['activo'] == 1 else "No", num_format)
            row_idx += 1

    # Pestaña 2: Personal y Perfiles
    ws2 = workbook.add_worksheet("Personal y Perfiles")
    ws2.write(0, 0, "PROFESIONALES Y REGLAS INDIVIDUALES", title_format)
    
    ws2.write(2, 0, "LISTADO DE PERSONAL", workbook.add_format({'bold': True, 'font_size': 12, 'font_color': '#1F497D'}))
    df_p = data["personal"]
    headers_pers = ["Nombre", "Categoría", "Rol", "Régimen Trabajo", "Horas Reg. Mensual", "Cumpleaños", "Madre", "Padre", "Puestos Habilitados"]
    for col_idx, h in enumerate(headers_pers):
        ws2.write(3, col_idx, h, header_format)
        
    row_idx = 4
    for _, r in df_p.iterrows():
        ws2.write(row_idx, 0, clean_val(r['nombre']), cell_format)
        ws2.write(row_idx, 1, clean_val(r['categoria']), num_format)
        ws2.write(row_idx, 2, clean_val(r['rol']), num_format)
        ws2.write(row_idx, 3, clean_val(r['regimen_trabajo']), num_format)
        ws2.write(row_idx, 4, clean_val(r['horas_mensuales_reglamentarias']), num_format)
        ws2.write(row_idx, 5, clean_val(r['fecha_cumpleanos']), num_format)
        ws2.write(row_idx, 6, "Sí" if r['es_madre'] == 1 else "No", num_format)
        ws2.write(row_idx, 7, "Sí" if r['es_padre'] == 1 else "No", num_format)
        ws2.write(row_idx, 8, clean_val(r['puestos']), cell_format)
        row_idx += 1

    row_idx += 1
    ws2.write(row_idx, 0, "REGLAS INDIVIDUALES ACTIVAS", workbook.add_format({'bold': True, 'font_size': 12, 'font_color': '#1F497D'}))
    row_idx += 1
    df_pr = data["reglas_personal"]
    headers_p_reg = ["Personal Nombre", "Código Regla", "Tipo", "Descripción", "Parámetros JSON"]
    for col_idx, h in enumerate(headers_p_reg):
        ws2.write(row_idx, col_idx, h, header_format)
        
    row_idx += 1
    if df_pr.empty:
        ws2.write(row_idx, 0, "(Sin reglas individuales específicas)", subtitle_format)
        row_idx += 1
    else:
        for _, r in df_pr.iterrows():
            ws2.write(row_idx, 0, clean_val(r['personal_nombre']), cell_format)
            ws2.write(row_idx, 1, clean_val(r['codigo_regla']), cell_format)
            ws2.write(row_idx, 2, clean_val(r['regla_tipo']), num_format)
            ws2.write(row_idx, 3, clean_val(r['regla_descripcion']), cell_format)
            ws2.write(row_idx, 4, clean_val(r['parametros_json']), cell_format)
            row_idx += 1

    # Pestaña 3: Ajustes Personales y Licencias
    ws3 = workbook.add_worksheet("Ajustes y Licencias")
    ws3.write(0, 0, "AJUSTES MENSUALES Y LICENCIAS", title_format)

    ws3.write(2, 0, "EXCEPCIONES / AJUSTES A REGLAS PERSONALES (MES SELECCIONADO)", workbook.add_format({'bold': True, 'font_size': 12, 'font_color': '#1F497D'}))
    df_ap = data["ajustes_personal"]
    headers_ap = ["Personal Nombre", "Código Regla", "Fecha Inicio", "Fecha Fin", "Acción", "Parámetros JSON"]
    for col_idx, h in enumerate(headers_ap):
        ws3.write(3, col_idx, h, header_format)
        
    row_idx = 4
    if df_ap.empty:
        ws3.write(row_idx, 0, "(Sin excepciones de reglas para el período)", subtitle_format)
        row_idx += 1
    else:
        for _, r in df_ap.iterrows():
            ws3.write(row_idx, 0, clean_val(r['personal_nombre']), cell_format)
            ws3.write(row_idx, 1, clean_val(r['codigo_regla']), cell_format)
            ws3.write(row_idx, 2, clean_val(r['fecha_inicio']), num_format)
            ws3.write(row_idx, 3, clean_val(r['fecha_fin']), num_format)
            ws3.write(row_idx, 4, clean_val(r['accion']), num_format)
            ws3.write(row_idx, 5, clean_val(r['parametros_json']), cell_format)
            row_idx += 1

    row_idx += 1
    ws3.write(row_idx, 0, "LICENCIAS ACTIVAS (MES SELECCIONADO)", workbook.add_format({'bold': True, 'font_size': 12, 'font_color': '#1F497D'}))
    row_idx += 1
    df_lic = data["licencias"]
    headers_lic = ["Nombre", "Tipo Licencia", "Fecha Inicio", "Fecha Fin", "Metadata/Motivo"]
    for col_idx, h in enumerate(headers_lic):
        ws3.write(row_idx, col_idx, h, header_format)
        
    row_idx += 1
    if df_lic.empty:
        ws3.write(row_idx, 0, "(Sin licencias cargadas para el período)", subtitle_format)
        row_idx += 1
    else:
        for _, r in df_lic.iterrows():
            ws3.write(row_idx, 0, clean_val(r['nombre']), cell_format)
            ws3.write(row_idx, 1, clean_val(r['tipo_licencia']), num_format)
            ws3.write(row_idx, 2, clean_val(r['fecha_inicio']), num_format)
            ws3.write(row_idx, 3, clean_val(r['fecha_fin']), num_format)
            ws3.write(row_idx, 4, clean_val(r['metadata']), cell_format)
            row_idx += 1

    row_idx += 1
    ws3.write(row_idx, 0, "ASIGNACIONES FIJAS PREVIAS / GUARDIAS APROBADAS EN EL PERÍODO", workbook.add_format({'bold': True, 'font_size': 12, 'font_color': '#1F497D'}))
    row_idx += 1
    df_g = data["guardias_previas"]
    headers_g = ["Nombre", "Fecha", "Turno", "Horas", "ID Cronograma Aprobado", "Notas Cronograma"]
    for col_idx, h in enumerate(headers_g):
        ws3.write(row_idx, col_idx, h, header_format)
        
    row_idx += 1
    if df_g.empty:
        ws3.write(row_idx, 0, "(Sin asignaciones previas aprobadas para el período)", subtitle_format)
        row_idx += 1
    else:
        for _, r in df_g.iterrows():
            ws3.write(row_idx, 0, clean_val(r['nombre']), cell_format)
            ws3.write(row_idx, 1, clean_val(r['fecha']), num_format)
            ws3.write(row_idx, 2, clean_val(r['turno']), num_format)
            ws3.write(row_idx, 3, clean_val(r['horas']), num_format)
            ws3.write(row_idx, 4, clean_val(r['cronograma_id']), num_format)
            ws3.write(row_idx, 5, clean_val(r['cronograma_notas']), cell_format)
            row_idx += 1

    # Pestaña 4: Demanda y Turnos
    ws4 = workbook.add_worksheet("Demanda y Turnos")
    ws4.write(0, 0, "CONFIGURACIÓN DE DEMANDA Y OFERTA DE TURNOS", title_format)

    ws4.write(2, 0, "DEMANDA BASE (VACANTES REQUERIDAS)", workbook.add_format({'bold': True, 'font_size': 12, 'font_color': '#1F497D'}))
    df_d = data["demanda"]
    headers_d = ["Puesto", "Tipo Día", "Hora Inicio", "Hora Fin", "Mínimo", "Máximo", "Días Habilitados"]
    for col_idx, h in enumerate(headers_d):
        ws4.write(3, col_idx, h, header_format)
        
    row_idx = 4
    for _, r in df_d.iterrows():
        ws4.write(row_idx, 0, clean_val(r['puesto']), cell_format)
        ws4.write(row_idx, 1, clean_val(r['tipo_dia']), num_format)
        ws4.write(row_idx, 2, clean_val(r['hora_inicio']), num_format)
        ws4.write(row_idx, 3, clean_val(r['hora_fin']), num_format)
        ws4.write(row_idx, 4, clean_val(r['cantidad_min']), num_format)
        ws4.write(row_idx, 5, clean_val(r['cantidad_max']), num_format)
        ws4.write(row_idx, 6, clean_val(r['dias_semana']), num_format)
        row_idx += 1

    row_idx += 1
    ws4.write(row_idx, 0, "AJUSTES DE DEMANDA PARA EL MES", workbook.add_format({'bold': True, 'font_size': 12, 'font_color': '#1F497D'}))
    row_idx += 1
    df_da = data["demanda_ajustes"]
    headers_da = ["Puesto", "Tipo Día", "Rango Horario", "Fecha Inicio", "Fecha Fin", "Mínimo", "Máximo", "Días Override"]
    for col_idx, h in enumerate(headers_da):
        ws4.write(row_idx, col_idx, h, header_format)
        
    row_idx += 1
    if df_da.empty:
        ws4.write(row_idx, 0, "(Sin ajustes de demanda en este mes)", subtitle_format)
        row_idx += 1
    else:
        for _, r in df_da.iterrows():
            ws4.write(row_idx, 0, clean_val(r['puesto']), cell_format)
            ws4.write(row_idx, 1, clean_val(r['tipo_dia']), num_format)
            ws4.write(row_idx, 2, f"{clean_val(r['hora_inicio'])} - {clean_val(r['hora_fin'])}", num_format)
            ws4.write(row_idx, 3, clean_val(r['fecha_inicio']), num_format)
            ws4.write(row_idx, 4, clean_val(r['fecha_fin']), num_format)
            ws4.write(row_idx, 5, clean_val(r['cantidad_min']), num_format)
            ws4.write(row_idx, 6, clean_val(r['cantidad_max']), num_format)
            ws4.write(row_idx, 7, clean_val(r['dias_semana_ajuste']), num_format)
            row_idx += 1

    row_idx += 1
    ws4.write(row_idx, 0, "OFERTA DE TURNOS CONFIGURADOS", workbook.add_format({'bold': True, 'font_size': 12, 'font_color': '#1F497D'}))
    row_idx += 1
    df_t = data["turnos"]
    headers_t = ["Nombre Turno", "Hora Inicio", "Duración (Horas)", "Días Semana Habilitados", "Puesto Asociado", "Orden"]
    for col_idx, h in enumerate(headers_t):
        ws4.write(row_idx, col_idx, h, header_format)
        
    row_idx += 1
    for _, r in df_t.iterrows():
        ws4.write(row_idx, 0, clean_val(r['turno_nombre']), cell_format)
        ws4.write(row_idx, 1, clean_val(r['hora_inicio']), num_format)
        ws4.write(row_idx, 2, clean_val(r['horas']), num_format)
        ws4.write(row_idx, 3, clean_val(r['dias_semana']), num_format)
        ws4.write(row_idx, 4, clean_val(r['puesto_nombre']), cell_format)
        ws4.write(row_idx, 5, clean_val(r['orden']), num_format)
        row_idx += 1

    row_idx += 1
    ws4.write(row_idx, 0, "AJUSTES TEMPORALES DE TURNOS / VACANTES", workbook.add_format({'bold': True, 'font_size': 12, 'font_color': '#1F497D'}))
    row_idx += 1
    df_ta = data["turnos_ajustes"]
    headers_ta = ["Nombre Turno", "Fecha Inicio", "Fecha Fin", "Vacantes", "Días Override"]
    for col_idx, h in enumerate(headers_ta):
        ws4.write(row_idx, col_idx, h, header_format)
        
    row_idx += 1
    if df_ta.empty:
        ws4.write(row_idx, 0, "(Sin ajustes temporales de vacantes de turnos)", subtitle_format)
        row_idx += 1
    else:
        for _, r in df_ta.iterrows():
            ws4.write(row_idx, 0, clean_val(r['turno_nombre']), cell_format)
            ws4.write(row_idx, 1, clean_val(r['fecha_inicio']), num_format)
            ws4.write(row_idx, 2, clean_val(r['fecha_fin']), num_format)
            ws4.write(row_idx, 3, clean_val(r['vacantes']), num_format)
            ws4.write(row_idx, 4, clean_val(r['dias_semana_ajuste']), num_format)
            row_idx += 1

    # Ajustar anchos de columnas automáticamente en todas las hojas
    for ws in [ws1, ws2, ws3, ws4]:
        # Habilitar gridlines para que sea más legible
        ws.hide_gridlines(2)
        
        # Ajuste de ancho de columnas dinámico
        # Este script busca el máximo tamaño para cada columna y lo aplica
        for i in range(12):  # Máximo de columnas analizadas
            # Hacemos set de columnas para ajustar de manera estándar
            ws.set_column(i, i, 16)
            
    # Hojas específicas con anchos más anchos
    ws1.set_column(0, 0, 22)
    ws1.set_column(2, 2, 45)
    ws1.set_column(3, 3, 30)
    
    ws2.set_column(0, 0, 25)
    ws2.set_column(3, 3, 35)
    ws2.set_column(4, 4, 30)

    ws3.set_column(0, 0, 25)
    ws3.set_column(5, 5, 30)

    ws4.set_column(0, 0, 20)
    ws4.set_column(3, 3, 20)
    ws4.set_column(4, 4, 20)

    writer.close()

def exportar_markdown(data, filename, servicio_nombre, fecha_str):
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"# Reporte de Auditoría de Configuración\n\n")
        f.write(f"- **Servicio:** {clean_val(data['servicio'].iloc[0]['servicio_nombre'])} (ID: {clean_val(data['servicio'].iloc[0]['servicio_id'])})\n")
        f.write(f"- **Organización:** {clean_val(data['servicio'].iloc[0]['organizacion_nombre'])}\n")
        f.write(f"- **Período a Auditar:** {fecha_str}\n")
        f.write(f"- **Fecha Generación:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("## 1. Resumen Servicio & Reglas Activas\n\n")
        f.write("### Reglas de Negocio Aplicables\n\n")
        
        df_reg = data["reglas_servicio"]
        if df_reg.empty:
            f.write("*(No se encontraron reglas activas)*\n\n")
        else:
            f.write("| Código Regla | Tipo | Origen | Activo | Descripción | Parámetros |\n")
            f.write("| --- | --- | --- | --- | --- | --- |\n")
            for _, r in df_reg.iterrows():
                f.write(f"| {clean_val(r['codigo_regla'])} | {clean_val(r['regla_tipo'])} | {clean_val(r['origen'])} | {'Sí' if r['activo'] == 1 else 'No'} | {clean_val(r['regla_descripcion'])} | `{clean_val(r['parametros_json']) or '{}'}` |\n")
            f.write("\n")
            
        f.write("### Ajustes Temporales de Servicio\n\n")
        df_aj_serv = data["ajustes_servicio"]
        if df_aj_serv.empty:
            f.write("*(Sin ajustes temporales del servicio en este período)*\n\n")
        else:
            f.write("| Código Regla | Inicio | Fin | Acción | Activo | Parámetros |\n")
            f.write("| --- | --- | --- | --- | --- | --- |\n")
            for _, r in df_aj_serv.iterrows():
                f.write(f"| {clean_val(r['codigo_regla'])} | {clean_val(r['fecha_inicio'])} | {clean_val(r['fecha_fin'])} | {clean_val(r['accion'])} | {'Sí' if r['activo'] == 1 else 'No'} | `{clean_val(r['parametros_json']) or '{}'}` |\n")
            f.write("\n")

        f.write("## 2. Personal y Perfiles\n\n")
        df_p = data["personal"]
        f.write("| Nombre | Categoría | Rol | Régimen | Horas Reg. | Cumpleaños | M/P | Puestos |\n")
        f.write("| --- | --- | --- | --- | --- | --- | --- | --- |\n")
        for _, r in df_p.iterrows():
            mp = "Madre" if r['es_madre'] == 1 else ("Padre" if r['es_padre'] == 1 else "-")
            f.write(f"| {clean_val(r['nombre'])} | {clean_val(r['categoria']) or '-'} | {clean_val(r['rol'])} | {clean_val(r['regimen_trabajo']) or '-'} | {clean_val(r['horas_mensuales_reglamentarias']) or '-'} | {clean_val(r['fecha_cumpleanos']) or '-'} | {mp} | {clean_val(r['puestos']) or '-'} |\n")
        f.write("\n")

        f.write("### Reglas Individuales de Personal\n\n")
        df_pr = data["reglas_personal"]
        if df_pr.empty:
            f.write("*(Sin reglas individuales activas)*\n\n")
        else:
            f.write("| Profesional | Código Regla | Tipo | Descripción | Parámetros |\n")
            f.write("| --- | --- | --- | --- | --- |\n")
            for _, r in df_pr.iterrows():
                f.write(f"| {clean_val(r['personal_nombre'])} | {clean_val(r['codigo_regla'])} | {clean_val(r['regla_tipo'])} | {clean_val(r['regla_descripcion'])} | `{clean_val(r['parametros_json']) or '{}'}` |\n")
            f.write("\n")

        f.write("## 3. Ajustes Personales & Licencias\n\n")
        f.write("### Ajustes Temporales de Reglas Personales\n\n")
        df_ap = data["ajustes_personal"]
        if df_ap.empty:
            f.write("*(Sin ajustes temporales de reglas de personal para este período)*\n\n")
        else:
            f.write("| Profesional | Código Regla | Inicio | Fin | Acción | Parámetros |\n")
            f.write("| --- | --- | --- | --- | --- | --- |\n")
            for _, r in df_ap.iterrows():
                f.write(f"| {clean_val(r['personal_nombre'])} | {clean_val(r['codigo_regla'])} | {clean_val(r['fecha_inicio'])} | {clean_val(r['fecha_fin'])} | {clean_val(r['accion'])} | `{clean_val(r['parametros_json']) or '{}'}` |\n")
            f.write("\n")

        f.write("### Licencias Cargadas\n\n")
        df_lic = data["licencias"]
        if df_lic.empty:
            f.write("*(Sin licencias activas en este período)*\n\n")
        else:
            f.write("| Profesional | Tipo | Inicio | Fin | Detalle |\n")
            f.write("| --- | --- | --- | --- | --- |\n")
            for _, r in df_lic.iterrows():
                f.write(f"| {clean_val(r['nombre'])} | {clean_val(r['tipo_licencia'])} | {clean_val(r['fecha_inicio'])} | {clean_val(r['fecha_fin'])} | {clean_val(r['metadata']) or '-'} |\n")
            f.write("\n")

        f.write("### Asignaciones Fijas / Guardias Aprobadas\n\n")
        df_g = data["guardias_previas"]
        if df_g.empty:
            f.write("*(Sin guardias aprobadas / asignaciones previas para este período)*\n\n")
        else:
            f.write("| Profesional | Fecha | Turno | Horas | ID Crono | Notas Cronograma |\n")
            f.write("| --- | --- | --- | --- | --- | --- |\n")
            for _, r in df_g.iterrows():
                f.write(f"| {clean_val(r['nombre'])} | {clean_val(r['fecha'])} | {clean_val(r['turno'])} | {clean_val(r['horas'])} | {clean_val(r['cronograma_id'])} | {clean_val(r['cronograma_notas']) or '-'} |\n")
            f.write("\n")

        f.write("## 4. Demanda y Oferta de Turnos\n\n")
        f.write("### Demanda Base (Vacantes Requeridas)\n\n")
        df_d = data["demanda"]
        f.write("| Puesto | Tipo Día | Hora Inicio | Hora Fin | Mínimo | Máximo | Días Habilitados |\n")
        f.write("| --- | --- | --- | --- | --- | --- | --- |\n")
        for _, r in df_d.iterrows():
            f.write(f"| {clean_val(r['puesto'])} | {clean_val(r['tipo_dia'])} | {clean_val(r['hora_inicio'])} | {clean_val(r['hora_fin'])} | {clean_val(r['cantidad_min'])} | {clean_val(r['cantidad_max'])} | {clean_val(r['dias_semana']) or '-'} |\n")
        f.write("\n")

        f.write("### Ajustes Temporales de Demanda\n\n")
        df_da = data["demanda_ajustes"]
        if df_da.empty:
            f.write("*(Sin ajustes de demanda activos en este período)*\n\n")
        else:
            f.write("| Puesto | Tipo Día | Rango | Inicio | Fin | Mínimo | Máximo | Días Override |\n")
            f.write("| --- | --- | --- | --- | --- | --- | --- | --- |\n")
            for _, r in df_da.iterrows():
                f.write(f"| {clean_val(r['puesto'])} | {clean_val(r['tipo_dia'])} | {clean_val(r['hora_inicio'])}-{clean_val(r['hora_fin'])} | {clean_val(r['fecha_inicio'])} | {clean_val(r['fecha_fin'])} | {clean_val(r['cantidad_min'])} | {clean_val(r['cantidad_max'])} | {clean_val(r['dias_semana_ajuste']) or '-'} |\n")
            f.write("\n")

        f.write("### Oferta de Turnos Configurada\n\n")
        df_t = data["turnos"]
        f.write("| Turno | Hora Inicio | Horas | Días Semana | Puesto | Orden |\n")
        f.write("| --- | --- | --- | --- | --- | --- |\n")
        for _, r in df_t.iterrows():
            f.write(f"| {clean_val(r['turno_nombre'])} | {clean_val(r['hora_inicio']) or '-'} | {clean_val(r['horas'])} | {clean_val(r['dias_semana']) or '-'} | {clean_val(r['puesto_nombre']) or '-'} | {clean_val(r['orden']) or '-'} |\n")
        f.write("\n")

        f.write("### Ajustes Temporales de Turnos / Vacantes\n\n")
        df_ta = data["turnos_ajustes"]
        if df_ta.empty:
            f.write("*(Sin ajustes temporales de turnos activos en este período)*\n\n")
        else:
            f.write("| Turno | Inicio | Fin | Vacantes | Días Override |\n")
            f.write("| --- | --- | --- | --- | --- |\n")
            for _, r in df_ta.iterrows():
                f.write(f"| {clean_val(r['turno_nombre'])} | {clean_val(r['fecha_inicio'])} | {clean_val(r['fecha_fin'])} | {clean_val(r['vacantes'])} | {clean_val(r['dias_semana_ajuste']) or '-'} |\n")
            f.write("\n")

def main():
    args = parse_args()
    fecha_inicio, fecha_fin, year, month = obtener_rango_mes(args.fecha)
    
    # Manejar conexión de base de datos
    db_path = args.db
    if not db_path:
        # Usar la conexión por defecto del proyecto
        conn = get_connection()
    else:
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA foreign_keys = ON")
    
    try:
        print(f"Buscando configuración para Servicio ID {args.servicio_id} en el período [{fecha_inicio} a {fecha_fin}]...")
        data = cargar_datos_auditoria(conn, args.servicio_id, fecha_inicio, fecha_fin)
        
        servicio_nombre = data["servicio"].iloc[0]['servicio_nombre']
        # Limpiar caracteres especiales para nombres de archivo
        serv_filename = "".join(c for c in servicio_nombre if c.isalnum() or c in (' ', '_', '-')).strip().replace(" ", "_")
        
        xls_filename = f"auditoria_config_{args.servicio_id}_{args.fecha}.xlsx"
        md_filename = f"auditoria_config_{args.servicio_id}_{args.fecha}.md"
        
        # Rutas completas de guardado
        # Se guardan en el directorio del script para fácil acceso
        xls_filepath = os.path.join(script_dir, xls_filename)
        md_filepath = os.path.join(script_dir, md_filename)
        
        print(f"Exportando a Excel: {xls_filename}...")
        exportar_excel(data, xls_filepath, servicio_nombre, args.fecha)
        
        print(f"Exportando a Markdown: {md_filename}...")
        exportar_markdown(data, md_filepath, servicio_nombre, args.fecha)
        
        print(f"\n[OK] Auditoría finalizada con éxito.")
        print(f"  - Excel: {xls_filepath}")
        print(f"  - Markdown: {md_filepath}")
        
    finally:
        conn.close()

if __name__ == "__main__":
    main()
