"""
sincronizar_sheets.py — Sincroniza francos forzados y asignaciones fijas
desde Google Sheets a la base de datos SQLite.

Columnas esperadas en la pestana "francos forzados":
    nombre | fecha_inicio | fecha_fin
    (si fecha_fin esta vacia, se asume franco de un solo dia)

Columnas esperadas en la pestana "asignaciones fijas":
    nombre | fecha | dia_semana | turno
    (fecha y dia_semana son mutuamente excluyentes)
"""

# ==============================================================================
# CONFIGURACION POR DEFECTO
# Modificar estas variables para ejecutar directamente sin argumentos CLI
# ==============================================================================
DEFAULT_SERVICIO_ID  = 2
DEFAULT_FECHA_INICIO = None   # None = sin filtro de fecha (sincroniza todo)
DEFAULT_FECHA_FIN    = None           # None = fin del mes de fecha_inicio (o sin filtro si inicio es None)
# ==============================================================================
import argparse
import calendar
import json
import os
import sys
import unicodedata
import urllib.request
import urllib.parse
from datetime import date, datetime, timedelta

# Fix encoding para consola Windows (cp1252 no soporta ciertos caracteres Unicode)
def _p(msg: str):
    """Print seguro para consola Windows: reemplaza caracteres no soportados."""
    print(msg.encode(sys.stdout.encoding or "utf-8", errors="replace").decode(sys.stdout.encoding or "utf-8", errors="replace"))

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


# ── Utilidades de texto ───────────────────────────────────────────────────────
def normalizar(texto: str) -> str:
    """Normaliza un texto: minúsculas, sin acentos, sin comas, sin puntos, sin espacios extras."""
    if not texto:
        return ""
    texto = str(texto).strip().lower()
    # Eliminar comas y puntos (la DB usa 'Apellido, Nombre' pero el Sheet puede no usarlos)
    texto = texto.replace(",", "").replace(".", "")
    # Colapsar espacios múltiples
    texto = " ".join(texto.split())
    nfkd = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def construir_mapa_personal(servicio_id: int) -> dict:
    """
    Retorna un dict {nombre_normalizado: nombre_exacto_db} del plantel activo
    del servicio, para resolver nombres del Sheet independientemente de
    mayúsculas/minúsculas y acentos.
    """
    personal = db_queries.obtener_personal_db(servicio_id)
    return {normalizar(p["Nombre"]): p["Nombre"] for p in personal}


def resolver_nombre(nombre_sheet: str, mapa_personal: dict) -> str | None:
    """Devuelve el nombre exacto de la DB o None si no se reconoce."""
    return mapa_personal.get(normalizar(nombre_sheet))


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
    Requiere que el Sheet sea público (lectura para cualquiera con el enlace).
    """
    rango = urllib.parse.quote(f"{pestana}!A:AZ")
    url = f"{SHEETS_API_BASE}/{spreadsheet_id}/values/{rango}?key={api_key}"
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data.get("values", [])
    except urllib.error.HTTPError as e:
        cuerpo = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"Error HTTP {e.code} leyendo hoja '{pestana}': {cuerpo[:300]}"
        )


def filas_a_dicts(filas: list[list]) -> list[dict]:
    """Convierte la primera fila como header y el resto como registros dict."""
    if not filas:
        return []
    headers = [h.strip().lower() for h in filas[0]]
    resultado = []
    for fila in filas[1:]:
        # Rellenar celdas vacías al final de la fila
        fila_ext = list(fila) + [""] * (len(headers) - len(fila))
        resultado.append(dict(zip(headers, [str(v).strip() for v in fila_ext])))
    return resultado


def parsear_fecha(texto: str) -> str | None:
    """Intenta parsear una fecha en varios formatos y devuelve 'YYYY-MM-DD' o None."""
    if not texto:
        return None
    formatos = ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d/%m/%y", "%d-%m-%y"]
    for fmt in formatos:
        try:
            return datetime.strptime(texto, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def fechas_solapan(fi1: str, ff1: str, fi2: str | None, ff2: str | None) -> bool:
    """Retorna True si los rangos [fi1,ff1] y [fi2,ff2] se solapan."""
    if fi2 is None or ff2 is None:
        return True
    return not (ff1 < fi2 or fi1 > ff2)


# ── Sincronización de Francos Forzados ───────────────────────────────────────
def sincronizar_francos(filas: list[dict], servicio_id: int,
                         fecha_inicio: str, fecha_fin: str,
                         mapa_personal: dict) -> dict:
    """
    Sincroniza la tabla personal_francos_forzados con los datos del Sheet.
    Política: inactivar registros existentes en el rango, luego reactivar o insertar.
    Retorna estadísticas del proceso.
    """
    stats = {"insertados": 0, "reactivados": 0, "inactivados": 0,
             "skipped_nombre": 0, "skipped_fecha": 0, "errores": 0}

    # Construir lista de francos válidos del Sheet
    francos_sheet = []
    for fila in filas:
        nombre_sheet = fila.get("nombre", "")
        fi_str = parsear_fecha(fila.get("fecha_inicio", ""))
        ff_str = parsear_fecha(fila.get("fecha_fin", ""))

        if not fi_str or not ff_str:
            # Si solo falta fecha_fin, asumir franco de un dia (fecha_fin = fecha_inicio)
            if fi_str and not ff_str:
                ff_str = fi_str
            else:
                _p(f"  [SKIP fecha] nombre='{nombre_sheet}' fi='{fila.get('fecha_inicio')}' ff='{fila.get('fecha_fin')}' (El formato de la fecha no es el correcto. Debe incluir año, ej: DD/MM/AAAA)")
                stats["skipped_fecha"] += 1
                continue

        nombre_db = resolver_nombre(nombre_sheet, mapa_personal)
        if not nombre_db:
            _p(f"  [SKIP nombre] '{nombre_sheet}' no reconocido en el plantel.")
            stats["skipped_nombre"] += 1
            continue

        # Solo incluir si el franco se solapa con el rango de mapeo
        if not fechas_solapan(fi_str, ff_str, fecha_inicio, fecha_fin):
            continue

        francos_sheet.append((nombre_db, fi_str, ff_str))

    with get_connection() as conn:
        # 1. Inactivar todos los registros del servicio que solapan el rango
        if fecha_inicio is None or fecha_fin is None:
            cur = conn.execute("""
                UPDATE personal_francos_forzados
                SET activo = 0
                WHERE servicio_id = ?
            """, (servicio_id,))
        else:
            cur = conn.execute("""
                UPDATE personal_francos_forzados
                SET activo = 0
                WHERE servicio_id = ?
                  AND NOT (fecha_fin < ? OR fecha_inicio > ?)
            """, (servicio_id, fecha_inicio, fecha_fin))
        stats["inactivados"] = cur.rowcount

        # 2. Para cada franco del Sheet: reactivar si existe, insertar si no
        for nombre_db, fi_str, ff_str in francos_sheet:
            cur_ex = conn.execute("""
                SELECT id FROM personal_francos_forzados
                WHERE personal_nombre = ? AND fecha_inicio = ? AND fecha_fin = ? AND servicio_id = ?
            """, (nombre_db, fi_str, ff_str, servicio_id))
            row = cur_ex.fetchone()
            if row:
                conn.execute("""
                    UPDATE personal_francos_forzados SET activo = 1 WHERE id = ?
                """, (row[0],))
                stats["reactivados"] += 1
            else:
                conn.execute("""
                    INSERT INTO personal_francos_forzados
                        (personal_nombre, fecha_inicio, fecha_fin, servicio_id, activo)
                    VALUES (?, ?, ?, ?, 1)
                """, (nombre_db, fi_str, ff_str, servicio_id))
                stats["insertados"] += 1

    return stats


# ── Sincronización de Asignaciones Fijas ─────────────────────────────────────
def sincronizar_asignaciones(filas: list[dict], servicio_id: int,
                              fecha_inicio: str, fecha_fin: str,
                              mapa_personal: dict) -> dict:
    """
    Sincroniza la tabla personal_asignaciones_fijas con los datos del Sheet.
    Separa eventuales (tienen 'fecha') de recurrentes (tienen 'dia_semana').
    Política: inactivar registros existentes, luego reactivar o insertar.
    Retorna estadísticas del proceso.
    """
    stats = {
        "eventuales_insertadas": 0, "eventuales_reactivadas": 0,
        "eventuales_inactivadas": 0,
        "recurrentes_insertadas": 0, "recurrentes_reactivadas": 0,
        "recurrentes_inactivadas": 0,
        "skipped_nombre": 0, "skipped_datos": 0
    }

    eventuales = []
    recurrentes = []

    dias_validos = {
        "lunes", "martes", "miercoles", "miércoles",
        "jueves", "viernes", "sabado", "sábado", "domingo"
    }

    for fila in filas:
        nombre_sheet = fila.get("nombre", "")
        fecha_str = parsear_fecha(fila.get("fecha", ""))
        dia_semana_raw = fila.get("dia_semana", "").strip()
        turno = fila.get("turno", "").strip().replace(" ", "_")

        if not turno:
            _p(f"  [SKIP turno vacio] nombre='{nombre_sheet}'")
            stats["skipped_datos"] += 1
            continue

        nombre_db = resolver_nombre(nombre_sheet, mapa_personal)
        if not nombre_db:
            _p(f"  [SKIP nombre] '{nombre_sheet}' no reconocido en el plantel.")
            stats["skipped_nombre"] += 1
            continue

        if fecha_str:
            # Eventual: solo incluir si cae en el rango de mapeo
            if fecha_inicio is None or fecha_fin is None or (fecha_inicio <= fecha_str <= fecha_fin):
                eventuales.append((nombre_db, fecha_str, turno))
        elif normalizar(dia_semana_raw) in {normalizar(d) for d in dias_validos}:
            # Normalizar nombre del dia con primera letra en mayuscula
            dia_norm = dia_semana_raw.capitalize()
            recurrentes.append((nombre_db, dia_norm, turno))
        else:
            _p(f"  [SKIP datos] nombre='{nombre_sheet}' sin fecha ni dia_semana valido.")
            stats["skipped_datos"] += 1

    with get_connection() as conn:
        # ── Eventuales ────────────────────────────────────────────────────────
        if fecha_inicio is None or fecha_fin is None:
            cur = conn.execute("""
                UPDATE personal_asignaciones_fijas
                SET activo = 0
                WHERE servicio_id = ? AND fecha IS NOT NULL
            """, (servicio_id,))
        else:
            cur = conn.execute("""
                UPDATE personal_asignaciones_fijas
                SET activo = 0
                WHERE servicio_id = ? AND fecha IS NOT NULL
                  AND fecha BETWEEN ? AND ?
            """, (servicio_id, fecha_inicio, fecha_fin))
        stats["eventuales_inactivadas"] = cur.rowcount

        for nombre_db, fecha_str, turno in eventuales:
            cur_ex = conn.execute("""
                SELECT id FROM personal_asignaciones_fijas
                WHERE personal_nombre = ? AND fecha = ? AND turno = ? AND servicio_id = ?
            """, (nombre_db, fecha_str, turno, servicio_id))
            row = cur_ex.fetchone()
            if row:
                conn.execute("UPDATE personal_asignaciones_fijas SET activo = 1 WHERE id = ?", (row[0],))
                stats["eventuales_reactivadas"] += 1
            else:
                conn.execute("""
                    INSERT INTO personal_asignaciones_fijas
                        (personal_nombre, fecha, dia_semana, turno, servicio_id, activo)
                    VALUES (?, ?, NULL, ?, ?, 1)
                """, (nombre_db, fecha_str, turno, servicio_id))
                stats["eventuales_insertadas"] += 1

        # ── Recurrentes ───────────────────────────────────────────────────────
        # Solo procesar si el Sheet tiene al menos una recurrente.
        # Si el Sheet no usa dia_semana (como en Servicio 3), no tocamos la DB.
        if recurrentes:
            cur = conn.execute("""
                UPDATE personal_asignaciones_fijas
                SET activo = 0
                WHERE servicio_id = ? AND dia_semana IS NOT NULL
            """, (servicio_id,))
            stats["recurrentes_inactivadas"] = cur.rowcount

            for nombre_db, dia_norm, turno in recurrentes:
                cur_ex = conn.execute("""
                    SELECT id FROM personal_asignaciones_fijas
                    WHERE personal_nombre = ? AND dia_semana = ? AND turno = ? AND servicio_id = ?
                """, (nombre_db, dia_norm, turno, servicio_id))
                row = cur_ex.fetchone()
                if row:
                    conn.execute("UPDATE personal_asignaciones_fijas SET activo = 1 WHERE id = ?", (row[0],))
                    stats["recurrentes_reactivadas"] += 1
                else:
                    conn.execute("""
                        INSERT INTO personal_asignaciones_fijas
                            (personal_nombre, fecha, dia_semana, turno, servicio_id, activo)
                        VALUES (?, NULL, ?, ?, ?, 1)
                    """, (nombre_db, dia_norm, turno, servicio_id))
                    stats["recurrentes_insertadas"] += 1
        else:
            print("      [INFO] Sin recurrentes en el Sheet. Registros existentes en DB no modificados.")

    return stats


# ── Sincronización de Licencias ──────────────────────────────────────────────
TIPOS_LICENCIA_VALIDOS = {"LPP", "LAR", "CM", "LM"}

def sincronizar_licencias(filas: list[dict], servicio_id: int,
                          fecha_inicio: str, fecha_fin: str,
                          mapa_personal: dict) -> dict:
    """
    Sincroniza la tabla licencias con los datos del Sheet.
    Columnas esperadas (acepta aliases):
      nombre | fecha_inicio (o "Inicio Licencia") | fecha_fin (o "Fin Licencia") | tipo (o "Tipo Licencia")
    Tipos validos: LPP, LAR, CM, LM.
    Politica: inactivar registros existentes en el rango, luego reactivar o insertar.
    """
    stats = {"insertadas": 0, "reactivadas": 0, "inactivadas": 0,
             "skipped_nombre": 0, "skipped_fecha": 0, "skipped_tipo": 0}

    # Aliases de headers: el Sheet puede llamar las columnas de distintas maneras.
    # La funcion _get resuelve el primero que encuentre en la fila (normalizado a lower).
    ALIAS_FI   = ["fecha_inicio", "inicio licencia", "inicio", "fecha inicio", "desde"]
    ALIAS_FF   = ["fecha_fin",    "fin licencia",    "fin",    "fecha fin",    "hasta"]
    ALIAS_TIPO = ["tipo",         "tipo licencia",   "tipo de licencia"]

    def _get(fila: dict, aliases: list) -> str:
        for a in aliases:
            v = fila.get(a, "")
            if v:
                return v
        return ""

    licencias_sheet = []
    for fila in filas:
        nombre_sheet = fila.get("nombre", "")
        fi_str = parsear_fecha(_get(fila, ALIAS_FI))
        ff_str = parsear_fecha(_get(fila, ALIAS_FF))
        tipo   = _get(fila, ALIAS_TIPO).strip().upper()

        if not fi_str or not ff_str:
            _p(f"  [SKIP fecha] nombre='{nombre_sheet}' fi='{fila.get('fecha_inicio')}' ff='{fila.get('fecha_fin')}' ")
            stats["skipped_fecha"] += 1
            continue

        if tipo not in TIPOS_LICENCIA_VALIDOS:
            _p(f"  [SKIP tipo] nombre='{nombre_sheet}' tipo='{tipo}' (validos: {sorted(TIPOS_LICENCIA_VALIDOS)})")
            stats["skipped_tipo"] += 1
            continue

        nombre_db = resolver_nombre(nombre_sheet, mapa_personal)
        if not nombre_db:
            _p(f"  [SKIP nombre] '{nombre_sheet}' no reconocido en el plantel.")
            stats["skipped_nombre"] += 1
            continue

        if not fechas_solapan(fi_str, ff_str, fecha_inicio, fecha_fin):
            continue

        licencias_sheet.append((nombre_db, fi_str, ff_str, tipo))

    with get_connection() as conn:
        # 1. Inactivar todas las licencias del servicio que solapan el rango
        if fecha_inicio is None or fecha_fin is None:
            cur = conn.execute("""
                UPDATE licencias
                SET activa = 0
                WHERE servicio_id = ?
            """, (servicio_id,))
        else:
            cur = conn.execute("""
                UPDATE licencias
                SET activa = 0
                WHERE servicio_id = ?
                  AND NOT (fecha_fin < ? OR fecha_inicio > ?)
            """, (servicio_id, fecha_inicio, fecha_fin))
        stats["inactivadas"] = cur.rowcount

        # 2. Reactivar o insertar
        for nombre_db, fi_str, ff_str, tipo in licencias_sheet:
            cur_ex = conn.execute("""
                SELECT id FROM licencias
                WHERE nombre = ? AND fecha_inicio = ? AND fecha_fin = ? AND tipo = ? AND servicio_id = ?
            """, (nombre_db, fi_str, ff_str, tipo, servicio_id))
            row = cur_ex.fetchone()
            if row:
                conn.execute("UPDATE licencias SET activa = 1 WHERE id = ?", (row[0],))
                stats["reactivadas"] += 1
            else:
                conn.execute("""
                    INSERT INTO licencias (nombre, fecha_inicio, fecha_fin, tipo, activa, servicio_id)
                    VALUES (?, ?, ?, ?, 1, ?)
                """, (nombre_db, fi_str, ff_str, tipo, servicio_id))
                stats["insertadas"] += 1

    return stats


# ── Sincronización de Exclusiones de Turnos ───────────────────────────────────
MAPA_DIAS = {
    "lunes": 0, "lun": 0, "0": 0,
    "martes": 1, "mar": 1, "1": 1,
    "miercoles": 2, "miércoles": 2, "mie": 2, "2": 2,
    "jueves": 3, "jue": 3, "3": 3,
    "viernes": 4, "vie": 4, "4": 4,
    "sabado": 5, "sábado": 5, "sab": 5, "5": 5,
    "domingo": 6, "dom": 6, "6": 6
}

def parsear_dias_exclusion(texto: str) -> list[int]:
    """Convierte una cadena de días separados por comas en una lista ordenada de enteros 0..6."""
    if not texto:
        return list(range(7))
    partes = [p.strip() for p in texto.split(",") if p.strip()]
    dias = []
    for p in partes:
        p_norm = normalizar(p)
        if p_norm in MAPA_DIAS:
            dias.append(MAPA_DIAS[p_norm])
    return sorted(list(set(dias)))


def parsear_turnos_exclusion(texto: str) -> list[str]:
    """Convierte una cadena de turnos separados por comas en una lista de siglas de turnos normalizadas."""
    if not texto:
        return []
    partes = [p.strip() for p in texto.split(",") if p.strip()]
    return [p.replace(" ", "_") for p in partes]


def obtener_exclusiones_base(personal_nombre: str, servicio_id: int) -> list:
    """
    Obtiene las exclusiones base para un empleado según la jerarquía:
    1. personal_reglas para el empleado.
    2. servicios_reglas para el servicio.
    """
    with get_connection() as conn:
        # 1. Intentar obtener de personal_reglas
        cur = conn.execute("""
            SELECT parametros_json 
            FROM personal_reglas 
            WHERE personal_nombre = ? AND codigo_regla = 'EXCLUIR_TURNOS' AND activo = 1
        """, (personal_nombre,))
        row = cur.fetchone()
        if row and row[0]:
            try:
                return json.loads(row[0])
            except Exception:
                pass
                
        # 2. Si no hay, intentar obtener de servicios_reglas
        cur = conn.execute("""
            SELECT parametros_json 
            FROM servicios_reglas 
            WHERE servicio_id = ? AND codigo_regla = 'EXCLUIR_TURNOS' AND activo = 1
        """, (servicio_id,))
        row = cur.fetchone()
        if row and row[0]:
            try:
                return json.loads(row[0])
            except Exception:
                pass
                
    return []


def normalizar_estructura_exclusiones(exclusiones: list) -> list:
    """Normaliza una lista de exclusiones ordenando las listas de turnos y dias para consistencia en la DB."""
    res = []
    for excl in exclusiones:
        if not isinstance(excl, dict):
            continue
        turnos = sorted([str(t).strip() for t in excl.get("turnos", [])])
        dias = []
        for d in excl.get("dias", []):
            try:
                dias.append(int(d))
            except ValueError:
                pass
        dias = sorted(list(set(dias)))
        res.append({"turnos": turnos, "dias": dias})
    
    # Eliminar duplicados estructurales
    unicos = []
    for r in res:
        if r not in unicos:
            unicos.append(r)
    return unicos


def sincronizar_exclusiones(filas: list[dict], servicio_id: int,
                            fecha_inicio: str, fecha_fin: str,
                            mapa_personal: dict) -> dict:
    """
    Sincroniza la tabla personal_reglas_ajustes con las exclusiones del Sheet.
    Combina las exclusiones del Sheet con las exclusiones base (servicio o personal fijo)
    para evitar que las reglas temporales anulen las exclusiones de 12 horas los fines de semana.
    Política: inactivar registros existentes en el rango de fecha para 'EXCLUIR_TURNOS',
    luego reactivar o insertar.
    """
    stats = {"insertados": 0, "reactivados": 0, "inactivados": 0,
             "skipped_nombre": 0, "skipped_fecha": 0}

    # Agrupar las exclusiones leídas del Sheet por (nombre_db, fecha_inicio, fecha_fin)
    grupos = {}  # clave: (nombre_db, fi, ff) -> valor: list of dicts {"turnos": [...], "dias": [...]}

    for fila in filas:
        nombre_sheet = fila.get("nombre", "")
        fi_str = parsear_fecha(fila.get("fecha_inicio", ""))
        ff_str = parsear_fecha(fila.get("fecha_fin", ""))
        dias_str = fila.get("dias", "")
        turno_str = fila.get("turno", "")

        if not fi_str or not ff_str:
            # Si solo falta fecha_fin, asumir exclusión de un día (fecha_fin = fecha_inicio)
            if fi_str and not ff_str:
                ff_str = fi_str
            else:
                _p(f"  [SKIP fecha] nombre='{nombre_sheet}' fi='{fila.get('fecha_inicio')}' ff='{fila.get('fecha_fin')}'")
                stats["skipped_fecha"] += 1
                continue

        nombre_db = resolver_nombre(nombre_sheet, mapa_personal)
        if not nombre_db:
            _p(f"  [SKIP nombre] '{nombre_sheet}' no reconocido en el plantel.")
            stats["skipped_nombre"] += 1
            continue

        # Solo incluir si solapa con el rango de mapeo
        if not fechas_solapan(fi_str, ff_str, fecha_inicio, fecha_fin):
            continue

        dias = parsear_dias_exclusion(dias_str)
        turnos = parsear_turnos_exclusion(turno_str)

        if not turnos:
            continue

        clave = (nombre_db, fi_str, ff_str)
        if clave not in grupos:
            grupos[clave] = []
        grupos[clave].append({"turnos": turnos, "dias": dias})

    with get_connection() as conn:
        # 1. Inactivar todos los ajustes de EXCLUIR_TURNOS del servicio que solapan el rango
        if fecha_inicio is None or fecha_fin is None:
            cur = conn.execute("""
                UPDATE personal_reglas_ajustes
                SET activo = 0
                WHERE servicio_id = ? AND codigo_regla = 'EXCLUIR_TURNOS'
            """, (servicio_id,))
        else:
            cur = conn.execute("""
                UPDATE personal_reglas_ajustes
                SET activo = 0
                WHERE servicio_id = ? AND codigo_regla = 'EXCLUIR_TURNOS'
                  AND NOT (fecha_fin < ? OR fecha_inicio > ?)
            """, (servicio_id, fecha_inicio, fecha_fin))
        stats["inactivados"] = cur.rowcount

        # 2. Para cada grupo, cargar base, hacer merge, normalizar y reactivar/insertar
        for (nombre_db, fi, ff), excl_list in grupos.items():
            # Cargar exclusiones base (personal o servicio)
            base_excl = obtener_exclusiones_base(nombre_db, servicio_id)
            
            # Combinar listas
            combinadas = normalizar_estructura_exclusiones(excl_list + base_excl)
            excl_json = json.dumps(combinadas)

            # Buscar si ya existe para reactivar
            cur_ex = conn.execute("""
                SELECT id FROM personal_reglas_ajustes
                WHERE personal_nombre = ? AND codigo_regla = 'EXCLUIR_TURNOS'
                  AND fecha_inicio = ? AND fecha_fin = ? AND parametros_json = ? AND servicio_id = ?
            """, (nombre_db, fi, ff, excl_json, servicio_id))
            row = cur_ex.fetchone()
            if row:
                conn.execute("""
                    UPDATE personal_reglas_ajustes SET activo = 1 WHERE id = ?
                """, (row[0],))
                stats["reactivados"] += 1
            else:
                conn.execute("""
                    INSERT INTO personal_reglas_ajustes
                        (personal_nombre, codigo_regla, fecha_inicio, fecha_fin, accion, parametros_json, activo, servicio_id)
                    VALUES (?, 'EXCLUIR_TURNOS', ?, ?, 'SOBRESCRIBIR', ?, 1, ?)
                """, (nombre_db, fi, ff, excl_json, servicio_id))
                stats["insertados"] += 1

    return stats


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="Sincroniza francos forzados y asignaciones fijas desde Google Sheets."
    )
    parser.add_argument("--servicio", type=int, default=DEFAULT_SERVICIO_ID,
                        help=f"ID del servicio (default: {DEFAULT_SERVICIO_ID})")
    parser.add_argument("--inicio", type=str, default=DEFAULT_FECHA_INICIO,
                        help="Fecha inicio del rango (YYYY-MM-DD). None = sin filtro.")
    parser.add_argument("--fin", type=str, default=DEFAULT_FECHA_FIN,
                        help="Fecha fin del rango (YYYY-MM-DD). None = fin del mes de inicio.")
    args = parser.parse_args()

    servicio_id  = args.servicio
    fecha_inicio = args.inicio
    fecha_fin    = args.fin

    # Si no hay fecha_inicio: sincronizar sin filtro de rango
    # Si hay fecha_inicio pero no fecha_fin: calcular fin del mes de inicio
    if fecha_inicio and not fecha_fin:
        dt = datetime.strptime(fecha_inicio, "%Y-%m-%d")
        ultimo_dia = calendar.monthrange(dt.year, dt.month)[1]
        fecha_fin = f"{dt.year}-{dt.month:02d}-{ultimo_dia:02d}"

    print("=" * 60)
    print(f"  SINCRONIZACION GOOGLE SHEETS -> SQLite")
    print(f"  Servicio ID : {servicio_id}")
    print(f"  Rango       : {fecha_inicio}  a  {fecha_fin}")
    print("=" * 60)

    # Inicializar la DB (migraciones seguras)
    db_schema.inicializar_db()

    # Cargar configuración
    try:
        config = cargar_config()
    except FileNotFoundError as e:
        print(f"[ERROR] {e}")
        sys.exit(1)

    api_key = config.get("api_key", "")
    if not api_key or api_key.startswith("PEGAR"):
        print("[ERROR] Completá la api_key en sheets_config.json antes de ejecutar.")
        sys.exit(1)

    servicio_cfg = config.get("servicios", {}).get(str(servicio_id))
    if not servicio_cfg:
        print(f"[ERROR] No hay configuración para el servicio_id={servicio_id} en sheets_config.json.")
        sys.exit(1)

    spreadsheet_id = servicio_cfg.get("spreadsheet_id", "")
    if not spreadsheet_id or spreadsheet_id.startswith("PEGAR"):
        print(f"[ERROR] Completá el spreadsheet_id del servicio {servicio_id} en sheets_config.json.")
        sys.exit(1)

    pestana_francos = servicio_cfg.get("pestana_francos", "francos forzados")
    pestana_asig    = servicio_cfg.get("pestana_asignaciones", "asignaciones fijas")
    pestana_lic     = servicio_cfg.get("pestana_licencias", "licencias")
    pestana_excl    = servicio_cfg.get("pestana_exclusiones", "exclusion turnos")

    # Construir mapa de personal
    mapa_personal = construir_mapa_personal(servicio_id)
    if not mapa_personal:
        print(f"[ERROR] No se encontró personal activo para el servicio {servicio_id}.")
        sys.exit(1)
    print(f"\n[INFO] Plantel cargado: {len(mapa_personal)} personas.")

    # ── Francos Forzados ──────────────────────────────────────────────────────
    print(f"\n[1/2] Leyendo pestaña '{pestana_francos}'...")
    try:
        filas_crudas = leer_hoja(spreadsheet_id, pestana_francos, api_key)
        filas_francos = filas_a_dicts(filas_crudas)
        print(f"      Filas leídas: {len(filas_francos)}")
        stats_f = sincronizar_francos(
            filas_francos, servicio_id, fecha_inicio, fecha_fin, mapa_personal
        )
        print(f"      Francos: inactivados={stats_f['inactivados']} | reactivados={stats_f['reactivados']} | insertados={stats_f['insertados']} | skip_nombre={stats_f['skipped_nombre']} | skip_fecha={stats_f['skipped_fecha']}")
    except Exception as e:
        print(f"[ERROR] Francos forzados: {e}")

    # ── Asignaciones Fijas ────────────────────────────────────────────────────
    print(f"\n[2/2] Leyendo pestana '{pestana_asig}'...")
    try:
        filas_crudas = leer_hoja(spreadsheet_id, pestana_asig, api_key)
        filas_asig = filas_a_dicts(filas_crudas)
        print(f"      Filas leidas: {len(filas_asig)}")
        stats_a = sincronizar_asignaciones(
            filas_asig, servicio_id, fecha_inicio, fecha_fin, mapa_personal
        )
        print(f"      Eventuales:  inactivadas={stats_a['eventuales_inactivadas']} | reactivadas={stats_a['eventuales_reactivadas']} | insertadas={stats_a['eventuales_insertadas']}")
        print(f"      Recurrentes: inactivadas={stats_a['recurrentes_inactivadas']} | reactivadas={stats_a['recurrentes_reactivadas']} | insertadas={stats_a['recurrentes_insertadas']}")
    except Exception as e:
        print(f"[ERROR] Asignaciones fijas: {e}")

    # ── Licencias ─────────────────────────────────────────────────────────────
    print(f"\n[3/3] Leyendo pestana '{pestana_lic}'...")
    try:
        filas_crudas = leer_hoja(spreadsheet_id, pestana_lic, api_key)
        filas_lic = filas_a_dicts(filas_crudas)
        print(f"      Filas leidas: {len(filas_lic)}")
        stats_l = sincronizar_licencias(
            filas_lic, servicio_id, fecha_inicio, fecha_fin, mapa_personal
        )
        print(f"      Licencias: inactivadas={stats_l['inactivadas']} | reactivadas={stats_l['reactivadas']} | insertadas={stats_l['insertadas']} | skip_nombre={stats_l['skipped_nombre']} | skip_fecha={stats_l['skipped_fecha']} | skip_tipo={stats_l['skipped_tipo']}")
    except Exception as e:
        print(f"[ERROR] Licencias: {e}")

    # ── Exclusiones de Turnos ──────────────────────────────────────────────────
    if pestana_excl:
        print(f"\n[4/4] Leyendo pestaña '{pestana_excl}'...")
        try:
            filas_crudas = leer_hoja(spreadsheet_id, pestana_excl, api_key)
            filas_excl = filas_a_dicts(filas_crudas)
            print(f"      Filas leídas: {len(filas_excl)}")
            stats_e = sincronizar_exclusiones(
                filas_excl, servicio_id, fecha_inicio, fecha_fin, mapa_personal
            )
            print(f"      Exclusiones: inactivados={stats_e['inactivados']} | reactivados={stats_e['reactivados']} | insertados={stats_e['insertados']} | skip_nombre={stats_e['skipped_nombre']} | skip_fecha={stats_e['skipped_fecha']}")
        except Exception as e:
            print(f"[ERROR] Exclusiones de turnos: {e}")

    print("\n[OK] Sincronizacion finalizada.")
    print("=" * 60)


if __name__ == "__main__":
    main()
