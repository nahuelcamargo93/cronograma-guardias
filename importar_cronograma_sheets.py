"""
importar_cronograma_sheets.py — Consume un cronograma desde Google Sheets
y crea un registro nuevo con su correspondiente id en la base de datos SQLite.
"""

# ==============================================================================
# CONFIGURACIÓN POR DEFECTO
# Modificar estas variables para cambiar los defaults o usar argumentos CLI
# ==============================================================================

DEFAULT_SERVICIO_ID  = 2
DEFAULT_FECHA_INICIO = "2026-07-01"
DEFAULT_FECHA_FIN    = None           # None = fin del mes de fecha_inicio
DEFAULT_VISTA        = "Personal"     # "personal" o "cronograma"
DEFAULT_SPREADSHEET_ID = "11oCu39JKyDCSS9YGkxzZgF6vB9mTJxb8vfbwDNQXPWU"
DEFAULT_NOTAS        = "Importado desde Google Sheets"

# ==============================================================================

import argparse
import calendar
import json
import os
import re
import sys
import unicodedata
import urllib.request
import urllib.parse
from datetime import datetime, date, timedelta
import pandas as pd

# ── Rutas del proyecto ────────────────────────────────────────────────────────
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from database.connection import get_connection
from database import schema as db_schema
from database import queries as db_queries

# ── Configuración ─────────────────────────────────────────────────────────────
CONFIG_PATH = os.path.join(PROJECT_ROOT, "sheets_config.json")
SHEETS_API_BASE = "https://sheets.googleapis.com/v4/spreadsheets"


def _p(msg: str):
    """Print seguro para consola Windows: reemplaza caracteres no soportados."""
    print(msg.encode(sys.stdout.encoding or "utf-8", errors="replace").decode(sys.stdout.encoding or "utf-8", errors="replace"))


# ── Utilidades de texto ───────────────────────────────────────────────────────
def normalizar(texto: str) -> str:
    """Normaliza un texto: minúsculas, sin acentos, sin comas, sin puntos, sin espacios extras."""
    if not texto:
        return ""
    texto = str(texto).strip().lower()
    texto = texto.replace(",", "").replace(".", "")
    texto = " ".join(texto.split())
    nfkd = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def construir_mapa_personal(servicio_id: int) -> dict:
    """Retorna un dict {nombre_normalizado: nombre_exacto_db} del plantel activo."""
    personal = db_queries.obtener_personal_db(servicio_id)
    return {normalizar(p["Nombre"]): p["Nombre"] for p in personal}


def resolver_nombre_personal(nombre_sheet: str, mapa_personal: dict) -> str | None:
    """
    Resuelve el nombre del personal en la DB a partir del texto del Sheet.
    Soporta coincidencia exacta normalizada y coincidencia parcial por apellido/nombre.
    """
    norm_sheet = normalizar(nombre_sheet)
    if not norm_sheet:
        return None

    # 1. Coincidencia exacta
    if norm_sheet in mapa_personal:
        return mapa_personal[norm_sheet]

    # 2. Coincidencia parcial (ej. si el Sheet solo tiene el apellido o parte del nombre)
    coincidencias = []
    for norm_db, nombre_real in mapa_personal.items():
        partes_db = norm_db.split()
        if norm_sheet in norm_db or any(norm_sheet == p for p in partes_db):
            coincidencias.append(nombre_real)

    if len(coincidencias) == 1:
        return coincidencias[0]
    elif len(coincidencias) > 1:
        # Priorizar si empieza con el término buscado
        coincidencias_priorizadas = [c for c in coincidencias if normalizar(c).startswith(norm_sheet)]
        if len(coincidencias_priorizadas) == 1:
            return coincidencias_priorizadas[0]
        
        _p(f"  [ADVERTENCIA] Nombre '{nombre_sheet}' ambiguo. Coincide con: {coincidencias}. Usando: {coincidencias[0]}")
        return coincidencias[0]

    return None


def resolver_nombre_turno(turno_sheet: str, siglas_invertido: dict, turnos_normalizados: dict) -> str | None:
    """Resuelve la sigla o nombre del turno al nombre oficial en la DB."""
    norm_turno = normalizar(turno_sheet)
    if not norm_turno:
        return None

    # 1. Buscar en siglas invertidas (ej. 'd_p' -> 'D_Planta')
    if norm_turno in siglas_invertido:
        return siglas_invertido[norm_turno]

    # 2. Buscar en nombres de turnos oficiales normalizados (ej. 'd_planta' -> 'D_Planta')
    if norm_turno in turnos_normalizados:
        return turnos_normalizados[norm_turno]

    return None


# ── Google Sheets API ─────────────────────────────────────────────────────────
def cargar_config() -> dict:
    """Lee sheets_config.json."""
    if not os.path.exists(CONFIG_PATH):
        raise FileNotFoundError(
            f"No se encontró {CONFIG_PATH}. Creá el archivo con tu api_key y spreadsheet_ids."
        )
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return json.load(f)


def leer_hoja(spreadsheet_id: str, pestana: str, api_key: str) -> list[list]:
    """
    Llama a la Sheets API v4 y devuelve los valores de la hoja como lista de listas.
    Aplica también celdas combinadas (merges) propagando el valor del origen.
    """
    rango = urllib.parse.quote(f"'{pestana}'!A:AZ")
    url = f"{SHEETS_API_BASE}/{spreadsheet_id}/values/{rango}?key={api_key}"
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        filas = data.get("values", [])
    except urllib.error.HTTPError as e:
        cuerpo = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"Error HTTP {e.code} leyendo hoja '{pestana}': {cuerpo[:300]}"
        )

    # Consultar y aplicar combinaciones de celdas (merges)
    try:
        url_merges = f"{SHEETS_API_BASE}/{spreadsheet_id}?fields=sheets(properties,merges)&key={api_key}"
        with urllib.request.urlopen(url_merges, timeout=15) as resp:
            meta = json.loads(resp.read().decode("utf-8"))
        
        hoja_meta = None
        for sheet in meta.get("sheets", []):
            if sheet.get("properties", {}).get("title") == pestana:
                hoja_meta = sheet
                break
                
        if hoja_meta:
            merges = hoja_meta.get("merges", [])
            for merge in merges:
                start_row = merge.get("startRowIndex", 0)
                end_row = merge.get("endRowIndex", 0)
                start_col = merge.get("startColumnIndex", 0)
                end_col = merge.get("endColumnIndex", 0)
                
                if start_row < len(filas) and start_col < len(filas[start_row]):
                    val = filas[start_row][start_col]
                    if val:
                        for r in range(start_row, min(end_row, len(filas))):
                            while len(filas[r]) < end_col:
                                filas[r].append("")
                            for c in range(start_col, end_col):
                                if r == start_row and c == start_col:
                                    continue
                                filas[r][c] = val
    except Exception as e:
        _p(f"  [ADVERTENCIA] No se pudieron aplicar celdas combinadas: {e}")
        
    return filas


def buscar_fila_de_fechas(filas: list[list], mes_default: int = 1) -> tuple[int, list[tuple[int, int, int]]]:
    """
    Busca la fila que contiene las cabeceras de fechas en formato d/m o d-m,
    o en su defecto números de día secuenciales (1 a 31).
    Retorna (indice_fila, [(col_idx, dia, mes), ...])
    """
    pattern = re.compile(r"^(\d+)[/\-](\d+)$")
    
    # 1. Intentar buscar patrón d/m o d-m
    for row_idx, fila in enumerate(filas):
        fechas_encontradas = []
        for col_idx, celda in enumerate(fila):
            val = str(celda).strip()
            match = pattern.match(val)
            if match:
                dia = int(match.group(1))
                mes = int(match.group(2))
                fechas_encontradas.append((col_idx, dia, mes))
                
        if len(fechas_encontradas) >= 5:
            return row_idx, fechas_encontradas
            
    # 2. Intentar buscar una fila con números secuenciales crecientes (ej. 1, 2, 3...)
    for row_idx, fila in enumerate(filas):
        fechas_encontradas = []
        for col_idx, celda in enumerate(fila):
            val = str(celda).strip()
            if val.isdigit():
                num = int(val)
                if 1 <= num <= 31:
                    fechas_encontradas.append((col_idx, num, mes_default))
                    
        if len(fechas_encontradas) >= 10:
            dias = [f[1] for f in fechas_encontradas]
            if all(dias[i] < dias[i+1] for i in range(len(dias)-1)):
                return row_idx, fechas_encontradas
                
    return -1, []


# ── Parsers de vistas ─────────────────────────────────────────────────────────
def procesar_vista_personal(filas: list[list], servicio_id: int, fecha_inicio: str,
                             mapa_personal: dict, siglas_invertido: dict,
                             turnos_normalizados: dict) -> list[dict]:
    """Parsea la Vista Personal y genera una lista de guardias."""
    base_dt = datetime.strptime(fecha_inicio, "%Y-%m-%d")
    idx_fechas, fechas_cols = buscar_fila_de_fechas(filas, base_dt.month)
    if idx_fechas == -1:
        raise ValueError("No se encontró la fila con cabeceras de fecha (formato d/m o d-m) en el Sheet.")

    anio_base = base_dt.year
    dias_nombres = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

    guardias = []

    # Procesar filas de personal
    for r_idx in range(idx_fechas + 1, len(filas)):
        row = filas[r_idx]
        if not row or not str(row[0]).strip():
            continue
        
        nombre_sheet = str(row[0]).strip()
        # Si la celda es un título de totalizadores o separadores, terminar la lectura
        if any(keyword in normalizar(nombre_sheet) for keyword in ["total", "referencia", "id cronograma", "guardias extra"]):
            break

        nombre_db = resolver_nombre_personal(nombre_sheet, mapa_personal)
        if not nombre_db:
            _p(f"  [SKIP nombre] '{nombre_sheet}' no reconocido en el plantel.")
            continue

        # Procesar columnas de fechas
        for col_idx, dia, mes in fechas_cols:
            if col_idx >= len(row):
                continue
            
            valor_celda = str(row[col_idx]).strip()
            if not valor_celda:
                continue

            # Si es franco o licencia, omitir la creación de la guardia
            norm_val = normalizar(valor_celda)
            if norm_val in ["f", "fs", "flr", "lar", "lpp", "lm", "cm", ""]:
                continue

            # Resolver el turno asignado
            turno_db = resolver_nombre_turno(valor_celda, siglas_invertido, turnos_normalizados)
            if not turno_db:
                _p(f"  [WARN turno] No se reconoce el turno/sigla '{valor_celda}' el día {dia}/{mes} para {nombre_db}.")
                continue

            # Construir la fecha exacta manejando el cambio de año (ej. de dic a ene)
            anio = anio_base
            if mes < base_dt.month and (base_dt.month - mes) > 6:
                anio = anio_base + 1
            elif mes > base_dt.month and (mes - base_dt.month) > 6:
                anio = anio_base - 1

            fecha_str = f"{anio}-{mes:02d}-{dia:02d}"
            dt_obj = datetime.strptime(fecha_str, "%Y-%m-%d")
            dia_semana_str = dias_nombres[dt_obj.weekday()]

            guardias.append({
                "Fecha": fecha_str,
                "Dia_Semana": dia_semana_str,
                "Turno": turno_db,
                "Personal": nombre_db
            })

    return guardias


def resolver_turno_cronograma(turno_sheet: str, nombre_personal: str, mapa_roles: dict,
                              siglas_invertido: dict, turnos_normalizados: dict,
                              nombres_turnos: list) -> str | None:
    """
    Deduce el turno oficial combinando el nombre del turno en la hoja
    con el rol del personal (útil en médicos donde 'Día' puede ser 'D_Planta' o 'D_Residente').
    """
    # 1. Intentar resolver de forma directa
    turno_directo = resolver_nombre_turno(turno_sheet, siglas_invertido, turnos_normalizados)
    if turno_directo:
        return turno_directo

    # 2. Si no, hacer deducción por coincidencia de palabras clave y rol
    norm_turno = normalizar(turno_sheet)
    rol = normalizar(mapa_roles.get(nombre_personal, ""))

    tipo_turno = None
    if "guardia" in norm_turno or norm_turno == "g":
        tipo_turno = "guardia"
    elif "noche" in norm_turno or norm_turno == "n":
        tipo_turno = "noche"
    elif "dia" in norm_turno or norm_turno == "d":
        tipo_turno = "dia"

    if tipo_turno:
        for t_oficial in nombres_turnos:
            t_norm = normalizar(t_oficial)
            
            match_tipo = False
            if tipo_turno == "dia" and (t_norm.startswith("d_") or t_norm.startswith("dia")):
                match_tipo = True
            elif tipo_turno == "guardia" and (t_norm.startswith("g_") or t_norm.startswith("guardia")):
                match_tipo = True
            elif tipo_turno == "noche" and (t_norm.startswith("n_") or t_norm.startswith("noche")):
                match_tipo = True

            if match_tipo:
                if "planta" in rol and "planta" in t_norm:
                    return t_oficial
                elif "residente" in rol and "residente" in t_norm:
                    return t_oficial
                elif "supervisor" in rol and "supervisor" in t_norm:
                    return t_oficial
                elif "monitorista" in rol and "monitorista" in t_norm:
                    return t_oficial

        # Fallback 1: Buscar cualquier turno oficial que comience con el tipo
        for t_oficial in nombres_turnos:
            t_norm = normalizar(t_oficial)
            if (tipo_turno == "dia" and (t_norm.startswith("d_") or t_norm.startswith("dia"))) or \
               (tipo_turno == "guardia" and (t_norm.startswith("g_") or t_norm.startswith("guardia"))) or \
               (tipo_turno == "noche" and (t_norm.startswith("n_") or t_norm.startswith("noche"))):
                _p(f"  [WARN] No se pudo deducir con precisión el turno oficial para '{nombre_personal}' en la fila del turno '{turno_sheet}' usando su rol '{rol}'. Aplicando fallback: se asignó el turno '{t_oficial}' por coincidencia de prefijo.")
                return t_oficial

    return None


def procesar_vista_cronograma(filas: list[list], servicio_id: int, fecha_inicio: str,
                              mapa_personal: dict, siglas_invertido: dict,
                              turnos_normalizados: dict, nombres_turnos: list,
                              mapa_roles: dict) -> list[dict]:
    """Parsea la Vista Cronograma y genera una lista de guardias."""
    base_dt = datetime.strptime(fecha_inicio, "%Y-%m-%d")
    anio_base = base_dt.year
    dias_nombres = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

    pattern_fecha = re.compile(r"^(\d+)[/\-](\d+)$")
    
    def obtener_fechas_fila(fila: list) -> list[tuple[int, int, int]] | None:
        fechas = []
        for col_idx, celda in enumerate(fila):
            val = str(celda).strip()
            match = pattern_fecha.match(val)
            if match:
                dia = int(match.group(1))
                mes = int(match.group(2))
                fechas.append((col_idx, dia, mes))
        if len(fechas) >= 5:
            return fechas
        return None

    guardias = []
    fechas_cols_activas = None
    ultimo_turno_sheet = ""

    # Procesar secuencialmente todas las filas
    for r_idx, row in enumerate(filas):
        if not row:
            continue

        # Intentar ver si la fila es una cabecera de fechas
        fechas_fila = obtener_fechas_fila(row)
        if fechas_fila is not None:
            fechas_cols_activas = fechas_fila
            ultimo_turno_sheet = "" # resetear propagación
            continue

        # Si no hay fechas activas detectadas todavía, ignorar fila
        if fechas_cols_activas is None:
            continue

        turno_sheet = str(row[0]).strip() if len(row) > 0 else ""
        if not turno_sheet:
            turno_sheet = ultimo_turno_sheet
        else:
            ultimo_turno_sheet = turno_sheet

        norm_turno = normalizar(turno_sheet)
        if not norm_turno or any(keyword in norm_turno for keyword in ["lpp", "lar", "lm", "cm", "referencia", "id cronograma", "total", "turno", "semana"]):
            continue

        # Procesar columnas de fechas
        for col_idx, dia, mes in fechas_cols_activas:
            if col_idx >= len(row):
                continue
            
            valor_celda = str(row[col_idx]).strip()
            if not valor_celda:
                continue

            # En la vista cronograma, las celdas pueden contener varios nombres separados por salto de línea
            nombres_en_celda = [n.strip() for n in valor_celda.split("\n") if n.strip()]
            
            for nombre_s in nombres_en_celda:
                nombre_db = resolver_nombre_personal(nombre_s, mapa_personal)
                if not nombre_db:
                    _p(f"  [SKIP nombre] '{nombre_s}' no reconocido en el plantel para la fila '{turno_sheet}'.")
                    continue

                # Resolver/deducir el turno oficial combinando la fila del turno y el rol del profesional
                turno_db = resolver_turno_cronograma(
                    turno_sheet, nombre_db, mapa_roles,
                    siglas_invertido, turnos_normalizados, nombres_turnos
                )
                if not turno_db:
                    _p(f"  [WARN turno] No se pudo deducir turno oficial para '{nombre_db}' en la fila '{turno_sheet}'.")
                    continue

                # Construir la fecha exacta
                anio = anio_base
                if mes < base_dt.month and (base_dt.month - mes) > 6:
                    anio = anio_base + 1
                elif mes > base_dt.month and (mes - base_dt.month) > 6:
                    anio = anio_base - 1

                fecha_str = f"{anio}-{mes:02d}-{dia:02d}"
                dt_obj = datetime.strptime(fecha_str, "%Y-%m-%d")
                dia_semana_str = dias_nombres[dt_obj.weekday()]

                guardias.append({
                    "Fecha": fecha_str,
                    "Dia_Semana": dia_semana_str,
                    "Turno": turno_db,
                    "Personal": nombre_db
                })

    return guardias


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="Importa un cronograma completo desde Google Sheets y crea uno nuevo en la DB."
    )
    parser.add_argument("--servicio", type=int, default=DEFAULT_SERVICIO_ID,
                        help=f"ID del servicio (default: {DEFAULT_SERVICIO_ID})")
    parser.add_argument("--inicio", type=str, default=DEFAULT_FECHA_INICIO,
                        help=f"Fecha inicio (YYYY-MM-DD, default: {DEFAULT_FECHA_INICIO})")
    parser.add_argument("--fin", type=str, default=DEFAULT_FECHA_FIN,
                        help="Fecha fin (YYYY-MM-DD). Default: fin del mes de inicio.")
    parser.add_argument("--vista", type=str, choices=["personal", "cronograma"], default=DEFAULT_VISTA,
                        help=f"Tipo de vista del Sheet (default: {DEFAULT_VISTA})")
    parser.add_argument("--sheet-id", type=str, default=None,
                        help="ID de la planilla Google Sheets (opcional, por defecto usa sheets_config.json)")
    parser.add_argument("--notas", type=str, default=DEFAULT_NOTAS,
                        help=f"Notas del cronograma (default: {DEFAULT_NOTAS})")
    parser.add_argument("--pestana", type=str, default=None,
                        help="Nombre exacto de la pestaña del Sheet a importar (sobrescribe la detección automática)")
    parser.add_argument("--tipo", type=str, choices=["PROGRAMADO", "REAL"], default="PROGRAMADO",
                        help="Tipo de cronograma a guardar (PROGRAMADO o REAL, default: PROGRAMADO)")
    args = parser.parse_args()

    servicio_id  = args.servicio
    fecha_inicio = args.inicio
    fecha_fin    = args.fin
    vista        = args.vista.lower()  # Asegurar minúsculas para el mapa de pestañas
    sheet_id     = args.sheet_id
    notas        = args.notas

    # Calcular fecha_fin si no está provista
    if fecha_inicio and not fecha_fin:
        dt = datetime.strptime(fecha_inicio, "%Y-%m-%d")
        ultimo_dia = calendar.monthrange(dt.year, dt.month)[1]
        fecha_fin = f"{dt.year}-{dt.month:02d}-{ultimo_dia:02d}"

    print("=" * 60)
    print(f"  IMPORTACIÓN DE NUEVO CRONOGRAMA")
    print(f"  Servicio ID : {servicio_id}")
    print(f"  Inicio      : {fecha_inicio}")
    print(f"  Fin         : {fecha_fin}")
    print(f"  Vista       : {vista}")
    print("=" * 60)

    # Inicializar la DB (migraciones seguras)
    db_schema.inicializar_db()

    # Cargar configuración de Sheets
    try:
        config = cargar_config()
    except FileNotFoundError as e:
        print(f"[ERROR] {e}")
        sys.exit(1)

    api_key = config.get("api_key", "")
    if not api_key or api_key.startswith("PEGAR"):
        print("[ERROR] Completá la api_key en sheets_config.json antes de ejecutar.")
        sys.exit(1)

    # Resolver spreadsheet_id (Priorizando DEFAULT_SPREADSHEET_ID del header)
    if not sheet_id or sheet_id.startswith("PEGAR") or sheet_id.strip() == "":
        if DEFAULT_SPREADSHEET_ID and not DEFAULT_SPREADSHEET_ID.startswith("PEGAR") and DEFAULT_SPREADSHEET_ID.strip() != "":
            sheet_id = DEFAULT_SPREADSHEET_ID
        else:
            servicio_cfg = config.get("servicios", {}).get(str(servicio_id))
            if servicio_cfg:
                sheet_id = servicio_cfg.get("spreadsheet_id", "")
        
        if not sheet_id or sheet_id.startswith("PEGAR"):
            print(f"[ERROR] Completá el spreadsheet_id del servicio {servicio_id} en sheets_config.json o el DEFAULT_SPREADSHEET_ID.")
            sys.exit(1)

    # Resolver pestaña adecuada según servicio y vista o parámetro CLI
    pestana = args.pestana
    if not pestana:
        pestanas_map = {
            1: {"cronograma": "Cronograma", "personal": "Vista por Personal"},
            2: {"cronograma": "Cronograma", "personal": "Vista Personal"},
            3: {"cronograma": "Cronograma", "personal": "Vista por Personal"},
            4: {"cronograma": "Cronograma", "personal": "Vista Personal"}
        }
        
        pestana = pestanas_map.get(servicio_id, {}).get(vista)
        if not pestana:
            pestana = "Vista por Personal" if vista == "personal" else "Cronograma"

    # Cargar mapas de personal y turnos para resolución
    mapa_personal = construir_mapa_personal(servicio_id)
    if not mapa_personal:
        print(f"[ERROR] No se encontró personal activo para el servicio {servicio_id}.")
        sys.exit(1)

    # Siglas de turnos
    siglas_map = db_queries.obtener_siglas_turnos(servicio_id)
    siglas_invertido = {normalizar(sigla): nombre for nombre, sigla in siglas_map.items()}

    # Turnos reales configurados
    with get_connection() as conn:
        rows_turnos = conn.execute("SELECT nombre FROM turnos_config WHERE servicio_id = ?", (servicio_id,)).fetchall()
    nombres_turnos = [r[0] for r in rows_turnos]
    turnos_normalizados = {normalizar(t): t for t in nombres_turnos}

    print(f"\n[INFO] Plantel cargado: {len(mapa_personal)} personas.")
    print(f"[INFO] Siglas cargadas: {len(siglas_map)} siglas de turnos.")
    print(f"[INFO] Leyendo hoja de Sheets: spreadsheet_id='{sheet_id}', pestaña='{pestana}'...")

    try:
        filas = leer_hoja(sheet_id, pestana, api_key)
    except Exception as e:
        print(f"[ERROR] No se pudo leer la hoja: {e}")
        sys.exit(1)

    print(f"[INFO] Total filas crudas leídas: {len(filas)}")

    # Parsear según la vista seleccionada
    try:
        if vista == "personal":
            guardias = procesar_vista_personal(
                filas, servicio_id, fecha_inicio,
                mapa_personal, siglas_invertido, turnos_normalizados
            )
        else:
            # Obtener roles de la base de datos
            personal_db = db_queries.obtener_personal_db(servicio_id)
            mapa_roles = {p['Nombre']: p['Rol'] for p in personal_db}
            
            guardias = procesar_vista_cronograma(
                filas, servicio_id, fecha_inicio,
                mapa_personal, siglas_invertido, turnos_normalizados,
                nombres_turnos, mapa_roles
            )
    except Exception as e:
        print(f"[ERROR] Al parsear el cronograma: {e}")
        sys.exit(1)

    print(f"\n[OK] Parseo finalizado. Se decodificaron {len(guardias)} guardias de trabajo.")

    if not guardias:
        print("[WARN] No se decodificó ninguna guardia. Abortando guardado.")
        sys.exit(0)

    # Persistencia en base de datos
    df_resultados = pd.DataFrame(guardias)
    
    # df_personal con nombres y roles
    personal_db = db_queries.obtener_personal_db(servicio_id)
    df_personal = pd.DataFrame(personal_db)
    
    # Calcular feriados e índices
    fecha_inicio_dt = datetime.strptime(fecha_inicio, "%Y-%m-%d")
    fecha_fin_dt = datetime.strptime(fecha_fin, "%Y-%m-%d")
    dias_del_bloque = (fecha_fin_dt - fecha_inicio_dt).days + 1
    offset_dia = fecha_inicio_dt.weekday()

    feriados_db = db_queries.obtener_feriados(fecha_inicio, fecha_fin, servicio_id=servicio_id)
    feriados_indices = []
    for f_str in feriados_db:
        f_dt = datetime.strptime(f_str, "%Y-%m-%d")
        delta = (f_dt - fecha_inicio_dt).days
        if 0 <= delta < dias_del_bloque:
            feriados_indices.append(delta)

    print(f"[INFO] Calculando fines de semana y feriados...")
    print(f"[INFO] Guardando nuevo cronograma en la base de datos...")

    try:
        cronograma_id = db_queries.guardar_cronograma(
            df_resultados, df_personal,
            fecha_inicio, fecha_fin,
            feriados_indices, offset_dia, dias_del_bloque,
            notas=notas,
            servicio_id=servicio_id,
            tipo=args.tipo.upper()
        )
        print("\n" + "=" * 60)
        print(f"  ¡NUEVO CRONOGRAMA CREADO CON ÉXITO!")
        print(f"  ID Cronograma : {cronograma_id}")
        print(f"  Notas         : {notas}")
        print("=" * 60)
    except Exception as e:
        print(f"[ERROR] No se pudo guardar el cronograma en la DB: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
