# ============================================================
# data.py — Configuración mínima del sistema
#
# IMPORTANTE: Toda la configuración de reglas (prohibiciones,
# seguimientos, asignaciones fijas, límites de horas, vacantes,
# etc.) se gestiona desde la base de datos (cronograma_inteligente.db).
# Este archivo solo contiene lo que NO puede vivir en la DB:
# el período activo, los parámetros de debug y la lista de personal.
# ============================================================

# --- PARÁMETROS DE DEPURACIÓN ---
DEBUG_LOGS                   = True
DEBUG_DISABLE_SEGUIMIENTO    = False  # Si True: desactiva reglas de semana de seguimiento
DEBUG_DISABLE_DESCANSO_NOCHE = False  # Si True: desactiva restriccion descanso post-noche
DEBUG_DISABLE_MAX_HORAS      = False  # Si True: desactiva limite de horas semanales

# --- PERÍODO DEL CRONOGRAMA ---
# FECHA_INICIO = "2026-05-25"
# FECHA_FIN    = "2026-07-05"  # Inclusive. El rango debe ser múltiplo de 7 días.
FECHA_INICIO = "2026-07-01"
FECHA_FIN    = "2026-07-31"

# --- SERVICIO ACTIVO ---
# ID del servicio para el cual se genera este cronograma y su reporte.
SERVICIO_ID = 2

# Lista de feriados en formato "YYYY-MM-DD"
FERIADOS = [
    "2026-05-25"
]

# --- FECHAS ESPECIALES (2026) ---
DIA_DEL_PADRE   = "2026-06-21"  # Tercer domingo de junio
DIA_DE_LA_MADRE = "2026-10-18"  # Tercer domingo de octubre

# --- PERSONAL ---
# El personal se carga dinámicamente desde la base de datos
# según el SERVICIO_ID activo.

# --- HELPERS ---
def asignar_horas(turno):
    """Devuelve las horas de un turno por su nombre."""
    if turno.startswith("Noche") or turno.startswith("Dia"):
        return 12
    return 6
