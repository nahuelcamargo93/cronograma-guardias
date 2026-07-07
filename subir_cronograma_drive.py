#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
subir_cronograma_drive.py — Genera el reporte Excel de un cronograma
y lo sube a Google Drive, con opción de convertirlo a Google Sheets nativo.
"""

import sqlite3
import pandas as pd
import sys
import os
import datetime
import argparse
import json

# Rutas del proyecto
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# ==============================================================================
# CONFIGURACIÓN POR DEFECTO PARA EJECUCIÓN DIRECTA (CLI)
# Modifica estas variables para no tener que tipearlas por consola
# ==============================================================================
DEFAULT_SERVICIO_ID   = 2  # Entero (1-4) o None para preguntar por consola
DEFAULT_CRONOGRAMA_ID  = 596  # Entero (ID) o None para preguntar por consola
DEFAULT_FOLDER_ID      = None  # ID de carpeta Drive o None para usar sheets_config.json
DEFAULT_NOMBRE         = None  # Nombre de archivo personalizado o None para usar el default
DEFAULT_NO_CONVERTIR   = False # True para subir como Excel crudo, False para convertir a Google Sheets
# ==============================================================================

from database import queries as db_queries
from database.data_loader import obtener_empleados
from utils import obtener_nombre_archivo

def _p(msg: str):
    """Print seguro para consola Windows: reemplaza caracteres no soportados."""
    print(msg.encode(sys.stdout.encoding or "utf-8", errors="replace").decode(sys.stdout.encoding or "utf-8", errors="replace"))

def cargar_config_drive(servicio_id: int = None) -> tuple[str, str, str]:
    """Carga archivos de secrets and token, y carpeta correspondiente al servicio desde sheets_config.json."""
    config_path = os.path.join(PROJECT_ROOT, "sheets_config.json")
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"No se encontró {config_path}.")
    with open(config_path, encoding="utf-8") as f:
        config = json.load(f)
    
    drive_cfg = config.get("drive", {})
    secrets_file = drive_cfg.get("client_secrets_file", "client_secrets.json")
    token_file = drive_cfg.get("token_file", "token.json")
    
    # Resolver rutas absolutas
    if not os.path.isabs(secrets_file):
        secrets_file = os.path.join(PROJECT_ROOT, secrets_file)
    if not os.path.isabs(token_file):
        token_file = os.path.join(PROJECT_ROOT, token_file)
        
    folder_id = ""
    if servicio_id is not None:
        servicio_cfg = config.get("servicios", {}).get(str(servicio_id), {})
        folder_id = servicio_cfg.get("folder_id", "")
        
    if folder_id.startswith("PEGAR_ID_CARPETA_DRIVE_") or folder_id.strip() == "":
        folder_id = ""
        
    return secrets_file, token_file, folder_id

def elegir_servicio() -> int:
    """Muestra un menú en consola para seleccionar el servicio."""
    print("\n=== SELECCIONAR SERVICIO ===")
    print("  1: Kinesiología Crítica")
    print("  2: Enfermería UTI")
    print("  3: Área Médica UTI")
    print("  4: Personal de Monitoreo (COM)")
    while True:
        try:
            val = input("Ingrese el ID del servicio (1-4): ").strip()
            if not val:
                continue
            servicio_id = int(val)
            if servicio_id in [1, 2, 3, 4]:
                return servicio_id
            print("[ERROR] ID de servicio inválido. Debe ser 1, 2, 3 o 4.")
        except (ValueError, KeyboardInterrupt):
            print("\nOperación cancelada.")
            sys.exit(0)

def elegir_cronograma(servicio_id: int) -> tuple[int, str, str]:
    """Muestra un menú para seleccionar el cronograma de la base de datos."""
    conn = sqlite3.connect(os.path.join(PROJECT_ROOT, 'cronograma_inteligente.db'))
    cursor = conn.cursor()
    
    # Consultar últimos cronogramas que tengan guardias asignadas para el servicio
    cursor.execute("""
        SELECT DISTINCT c.id, c.fecha_inicio, c.fecha_fin, c.notas, c.estado
        FROM cronogramas c
        JOIN guardias g ON c.id = g.cronograma_id
        JOIN personal p ON g.nombre = p.nombre
        WHERE p.servicio_id = ?
        ORDER BY c.id DESC
        LIMIT 10
    """, (servicio_id,))
    
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        _p(f"[ERROR] No se encontró ningún cronograma para el Servicio {servicio_id} en la base de datos.")
        sys.exit(1)
        
    print("\n=== SELECCIONAR CRONOGRAMA A EXPORTAR ===")
    for idx, r in enumerate(rows):
        c_id, f_ini, f_fin, notas, estado = r
        notas_str = f" - '{notas}'" if notas else ""
        print(f"  {idx + 1}: Opción {idx + 1} | Cronograma ID {c_id} ({f_ini} a {f_fin}) | Estado: {estado}{notas_str}")
        
    while True:
        try:
            val = input(f"Seleccione una opción (1-{len(rows)}) o ingrese directamente el ID de cronograma: ").strip()
            if not val:
                continue
            
            # Chequear si ingresó una opción del menú o un ID directo
            num_seleccionado = int(val)
            if 1 <= num_seleccionado <= len(rows):
                selected_row = rows[num_seleccionado - 1]
                return selected_row[0], selected_row[1], selected_row[2]
            
            # Si no está en el rango de opciones, buscarlo como ID absoluto
            conn = sqlite3.connect(os.path.join(PROJECT_ROOT, 'cronograma_inteligente.db'))
            cursor = conn.cursor()
            crono_exist = cursor.execute("""
                SELECT id, fecha_inicio, fecha_fin 
                FROM cronogramas 
                WHERE id = ?
            """, (num_seleccionado,)).fetchone()
            conn.close()
            
            if crono_exist:
                return crono_exist[0], crono_exist[1], crono_exist[2]
                
            print(f"[ERROR] Opción o ID de cronograma no válido.")
        except (ValueError, KeyboardInterrupt):
            print("\nOperación cancelada.")
            sys.exit(0)

def obtener_detalles_cronograma(crono_id: int) -> tuple[int, str, str]:
    """Obtiene fecha_inicio, fecha_fin y servicio_id de un cronograma forzado."""
    conn = sqlite3.connect(os.path.join(PROJECT_ROOT, 'cronograma_inteligente.db'))
    cursor = conn.cursor()
    
    crono = cursor.execute("""
        SELECT id, fecha_inicio, fecha_fin
        FROM cronogramas
        WHERE id = ?
    """, (crono_id,)).fetchone()
    
    if not crono:
        _p(f"[ERROR] No se encontró el Cronograma ID {crono_id} en la base de datos.")
        conn.close()
        sys.exit(1)
        
    # Obtener el servicio_id a partir del personal de las guardias de ese cronograma
    servicio_row = cursor.execute("""
        SELECT DISTINCT p.servicio_id
        FROM guardias g
        JOIN personal p ON g.nombre = p.nombre
        WHERE g.cronograma_id = ?
        LIMIT 1
    """, (crono_id,)).fetchone()
    
    conn.close()
    
    if not servicio_row:
        _p(f"[ERROR] No se pudo determinar el servicio para el Cronograma ID {crono_id} (no tiene guardias asignadas).")
        sys.exit(1)
        
    return servicio_row[0], crono[1], crono[2]

def generar_excel_local(servicio_id: int, crono_id: int, fecha_inicio: str, fecha_fin: str, nombre_personalizado: str = None) -> str:
    """Genera el archivo excel local usando el reporte correspondiente al servicio."""
    conn = sqlite3.connect(os.path.join(PROJECT_ROOT, 'cronograma_inteligente.db'))
    cursor = conn.cursor()

    # 1. Cargar df_resultados
    df_resultados = pd.read_sql_query("""
        SELECT fecha as Fecha, nombre as Personal, turno as Turno
        FROM guardias
        WHERE cronograma_id = ?
    """, conn, params=(crono_id,))

    # Agregar Dia_Semana
    dias_nombres = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    df_resultados['Dia_Semana'] = df_resultados['Fecha'].apply(
        lambda f: dias_nombres[datetime.datetime.strptime(f, "%Y-%m-%d").weekday()]
    )

    # Calcular variables de fecha
    fecha_inicio_dt = datetime.datetime.strptime(fecha_inicio, "%Y-%m-%d")
    fecha_fin_dt = datetime.datetime.strptime(fecha_fin, "%Y-%m-%d")
    total_dias = (fecha_fin_dt - fecha_inicio_dt).days + 1
    num_semanas = (total_dias + 6) // 7

    feriados_db = db_queries.obtener_feriados(fecha_inicio, fecha_fin, servicio_id=servicio_id)
    feriados_indices = []
    for f_str in feriados_db:
        f_dt = datetime.datetime.strptime(f_str, "%Y-%m-%d")
        delta = (f_dt - fecha_inicio_dt).days
        if 0 <= delta < total_dias:
            feriados_indices.append(delta)

    # 2. Cargar df_personal y turnos
    config_turnos, _, _, _ = db_queries.cargar_configuracion_turnos(
        servicio_id=servicio_id, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin
    )
    # Cargar licencias en memoria
    db_queries.init_licencias(servicio_id)
    empleados = obtener_empleados(servicio_id, fecha_inicio, total_dias)
    offset_dia = fecha_inicio_dt.weekday()

    df_personal = pd.DataFrame([vars(e) for e in empleados])
    df_personal = df_personal.rename(columns={'nombre': 'Nombre', 'rol': 'Rol'})

    # 3. Cargar semanas_categorias (df_cat_semanas) si el servicio lo usa
    df_cat_semanas = pd.read_sql_query("""
        SELECT nombre as Nombre, fecha_lunes as Fecha_Lunes, categoria as Categoria
        FROM semanas_categorias
        WHERE cronograma_id = ?
    """, conn, params=(crono_id,))

    # 4. Cargar flr_asignados
    cursor.execute("""
        SELECT nombre, fecha_inicio, fecha_fin
        FROM flr_asignados
        WHERE cronograma_id = ?
    """, (crono_id,))
    flrs_rows = cursor.fetchall()
    flrs_asignados = [{'nombre': r[0], 'fecha_inicio': r[1], 'fecha_fin': r[2]} for r in flrs_rows]

    conn.close()

    # Definir nombre de archivo base por defecto si no hay personalizado
    nombres_por_defecto = {
        1: 'Cronograma_Servicio_Kinesiologia.xlsx',
        2: 'Cronograma_Enfermeria_UTI.xlsx',
        3: 'Cronograma_Area_Medica_UTI.xlsx',
        4: 'Cronograma_Servicio_COM.xlsx'
    }
    
    base_file_name = nombre_personalizado or nombres_por_defecto[servicio_id]
    local_filename = obtener_nombre_archivo(base_file_name, fecha_inicio)
    
    # Asegurar que esté en la raíz del proyecto para coincidir con exportar_ultimo_cronograma.py
    local_filepath = os.path.join(PROJECT_ROOT, local_filename)

    _p(f"\n[INFO] Generando archivo Excel local: '{local_filepath}'...")
    
    if servicio_id == 1:
        from reportes.servicio_1_kinesiologia.kinesiologia import generar_y_exportar as gen_kin
        gen_kin(df_resultados, df_personal, total_dias, feriados_indices, fecha_inicio, offset_dia, config_turnos, num_semanas, file_name=local_filepath, crono_id=crono_id)
    elif servicio_id == 2:
        from reportes.servicio_2_enfermeria.enfermeria import generar_y_exportar as gen_enf
        gen_enf(df_resultados, df_personal, total_dias, feriados_indices, fecha_inicio, offset_dia, config_turnos, num_semanas, flrs_asignados, df_cat_semanas, file_name=local_filepath, crono_id=crono_id)
    elif servicio_id == 3:
        from reportes.servicio_3_medicos.medicos import generar_y_exportar as gen_med
        gen_med(df_resultados, df_personal, total_dias, feriados_indices, fecha_inicio, offset_dia, config_turnos, num_semanas, flrs_asignados, df_cat_semanas, file_name=local_filepath, crono_id=crono_id)
    elif servicio_id == 4:
        from reportes.servicio_4_monitoreo.com import generar_y_exportar as gen_com
        gen_com(df_resultados, df_personal, total_dias, feriados_indices, fecha_inicio, offset_dia, config_turnos, num_semanas, file_name=local_filepath, crono_id=crono_id)

    return local_filepath

def subir_a_drive(local_filepath: str, nombre_drive: str, folder_id: str, secrets_file: str, token_file: str, convert: bool = True) -> tuple[str, str]:
    """Sube el archivo Excel local a Google Drive usando autenticación OAuth 2.0."""
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload

    scopes = ["https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]
    creds = None

    # El archivo token.json almacena los tokens de acceso y actualización del usuario
    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, scopes)

    # Si no hay credenciales válidas disponibles, permitir que el usuario inicie sesión
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            _p("[INFO] El token de acceso ha expirado. Refrescándolo...")
            try:
                creds.refresh(Request())
            except Exception as e:
                _p(f"[WARN] Error al refrescar token: {e}. Iniciando flujo de autorización nuevo...")
                creds = None
                
        if not creds:
            if not os.path.exists(secrets_file):
                _p(f"\n[ERROR] No se encontró el archivo de secretos del cliente OAuth: '{secrets_file}'")
                _p("Para solucionar esto:")
                _p("  1. Entra a Google Cloud Console y ve a APIs y Servicios > Credenciales.")
                _p("  2. Crea un ID de cliente de OAuth 2.0 (Tipo de aplicación: Aplicación de escritorio / Desktop app).")
                _p("  3. Descarga el JSON de credenciales y guárdalo como 'client_secrets.json' en la raíz.")
                sys.exit(1)
                
            _p("\n[INFO] Iniciando el flujo de autorización web. Por favor, inicia sesión en tu navegador...")
            flow = InstalledAppFlow.from_client_secrets_file(secrets_file, scopes)
            creds = flow.run_local_server(port=0)
            
        # Guardar las credenciales para la próxima ejecución
        with open(token_file, "w") as token:
            token.write(creds.to_json())
            _p(f"[INFO] Credenciales guardadas en '{token_file}' para futuras ejecuciones.")

    service = build("drive", "v3", credentials=creds)
    
    file_metadata = {
        "name": nombre_drive
    }
    
    if folder_id:
        file_metadata["parents"] = [folder_id]
        _p(f"[INFO] Carpeta destino configurada (ID: {folder_id})")
    else:
        _p("[WARN] No se especificó ID de carpeta de Drive. El archivo se subirá al directorio raíz de tu Drive.")
        
    if convert:
        file_metadata["mimeType"] = "application/vnd.google-apps.spreadsheet"
        _p("[INFO] El archivo será convertido a formato Google Sheets al subir.")
    else:
        _p("[INFO] El archivo será subido como archivo binario Excel (.xlsx) nativo.")
        
    media = MediaFileUpload(
        local_filepath,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        resumable=True
    )
    
    # Buscar si ya existe un archivo con el mismo nombre y en la misma carpeta
    query = f"name = '{nombre_drive}' and trashed = false"
    if folder_id:
        query += f" and '{folder_id}' in parents"
        
    _p(f"[INFO] Buscando archivo existente en Drive con nombre '{nombre_drive}'...")
    results = service.files().list(
        q=query,
        spaces="drive",
        fields="files(id, webViewLink)",
        supportsAllDrives=True,
        includeItemsFromAllDrives=True
    ).execute()
    
    files = results.get("files", [])
    
    if files:
        existing_file_id = files[0].get("id")
        _p(f"[INFO] Archivo existente encontrado (ID: {existing_file_id}). Reemplazando contenido...")
        file = service.files().update(
            fileId=existing_file_id,
            media_body=media,
            fields="id, webViewLink",
            supportsAllDrives=True
        ).execute()
    else:
        _p(f"[INFO] No se encontró archivo existente. Subiendo nuevo archivo...")
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields="id, webViewLink",
            supportsAllDrives=True
        ).execute()
        
    return file.get("id"), file.get("webViewLink")

def main():
    parser = argparse.ArgumentParser(
        description="Genera el reporte de un cronograma y lo sube a Google Drive."
    )
    parser.add_argument("--servicio", type=int, default=DEFAULT_SERVICIO_ID,
                        help="ID del servicio (1: Kinesiología, 2: Enfermería, 3: Médicos, 4: COM).")
    parser.add_argument("--crono-id", type=int, default=DEFAULT_CRONOGRAMA_ID,
                        help="ID de cronograma forzado. Si se omite, se presentará un menú interactivo.")
    parser.add_argument("--folder-id", type=str, default=DEFAULT_FOLDER_ID,
                        help="ID de la carpeta Google Drive (si se omite, se usa el de sheets_config.json).")
    parser.add_argument("--nombre", type=str, default=DEFAULT_NOMBRE,
                        help="Nombre del archivo en Google Drive (si se omite, se usa el nombre por defecto del reporte).")
    parser.add_argument("--no-convertir", action="store_true", default=DEFAULT_NO_CONVERTIR,
                        help="Subir el Excel binario sin convertirlo a formato nativo Google Sheets.")
    
    args = parser.parse_args()
    
    servicio_id = args.servicio
    crono_id = args.crono_id
    folder_id = args.folder_id
    nombre_personalizado = args.nombre
    convertir = not args.no_convertir

    # Flujo interactivo si falta información clave
    if crono_id is not None:
        servicio_id, fecha_inicio, fecha_fin = obtener_detalles_cronograma(crono_id)
    else:
        if servicio_id is None:
            servicio_id = elegir_servicio()
        crono_id, fecha_inicio, fecha_fin = elegir_cronograma(servicio_id)

    # Cargar configuraciones de Drive desde el JSON para el servicio seleccionado
    try:
        secrets_file, token_file, resolved_folder_id = cargar_config_drive(servicio_id)
        if not folder_id:
            folder_id = resolved_folder_id
    except Exception as e:
        _p(f"[ERROR] Al leer sheets_config.json: {e}")
        sys.exit(1)

    if not folder_id:
        _p(f"[ERROR] No se configuró un ID de carpeta ('folder_id') válido para el servicio {servicio_id} en sheets_config.json.")
        _p("Por favor, edita 'sheets_config.json' para asignarle el ID correspondiente.")
        sys.exit(1)

    print("=" * 60)
    print(f"  EXPORTACIÓN A GOOGLE DRIVE")
    print(f"  Servicio ID   : {servicio_id}")
    print(f"  Cronograma ID : {crono_id}")
    print(f"  Período       : {fecha_inicio} al {fecha_fin}")
    print("=" * 60)

    # 1. Generar reporte local (.xlsx)
    try:
        local_filepath = generar_excel_local(servicio_id, crono_id, fecha_inicio, fecha_fin, nombre_personalizado)
        _p(f"[OK] Reporte generado localmente con éxito: '{local_filepath}'")
    except Exception as e:
        _p(f"[ERROR] Error al generar el Excel: {e}")
        sys.exit(1)

    # 2. Subir a Google Drive
    nombre_drive = os.path.basename(local_filepath)
    # Quitar la extensión .xlsx del nombre en Drive si se va a convertir
    if convertir and nombre_drive.endswith(".xlsx"):
        nombre_drive = nombre_drive[:-5]
        
    try:
        file_id, web_link = subir_a_drive(local_filepath, nombre_drive, folder_id, secrets_file, token_file, convertir)
        print("\n" + "=" * 60)
        _p(f"  ¡SUBIDA COMPLETADA CON ÉXITO!")
        _p(f"  ID de Archivo : {file_id}")
        _p(f"  Enlace Web    : {web_link}")
        print("=" * 60)
    except Exception as e:
        _p(f"[ERROR] Error al subir el archivo a Google Drive: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
