# ============================================================
# data.py — Configuración mínima del sistema
#
# IMPORTANTE: Toda la configuración de reglas (prohibiciones,
# seguimientos, asignaciones fijas, límites de horas, vacantes,
# etc.) se gestiona desde la base de datos (cronograma_inteligente.db).
# Este archivo solo contiene lo que NO puede vivir en la DB:
# el período activo, los parámetros de debug y la lista de personal.
# ============================================================

# --- PARÁMETROS DE DEPURACIÓN Y CONFIGURACIÓN DE REGLAS ---
DEBUG_LOGS                   = False
DEBUG_DISABLE_SEGUIMIENTO    = False  # Si True: desactiva reglas de semana de seguimiento
DEBUG_DISABLE_DESCANSO_NOCHE = False  # Si True: desactiva restriccion descanso post-noche
DEBUG_DISABLE_MAX_HORAS      = False  # Si True: desactiva limite de horas semanales

# --- CONFIGURACIÓN DE MEZCLA DE TURNOS EN LA SEMANA ---
# Si es True: se prohíbe mezclar turnos en la misma semana (regla dura).
# Si es False: se permite pero con una penalización alta (regla blanda).
EVITAR_MEZCLA_SEMANAL_DURA   = False
PESO_MEZCLA_SEMANAL_SOFT     = 50000

# --- CONFIGURACIÓN DE ROTACIÓN MENSUAL DE TURNOS ---
# Si es True: se obliga a rotar por todos los turnos (M, T, TN, N) en el mes (regla dura).
# Si es False: se permite no rotar pero con una penalización alta (regla blanda).
ROTACION_MENSUAL_DURA        = False
PESO_ROTACION_MENSUAL_SOFT   = 50000


# --- PERÍODO DEL CRONOGRAMA ---
# FECHA_INICIO = "2026-05-25"
# FECHA_FIN    = "2026-07-05"  # Inclusive. El rango debe ser múltiplo de 7 días.
FECHA_INICIO = "2026-06-01"
FECHA_FIN    = "2026-06-30"

# --- SERVICIO ACTIVO ---
# ID del servicio para el cual se genera este cronograma y su reporte.
SERVICIO_ID = 3

# Lista de feriados en formato "YYYY-MM-DD"
FERIADOS = [
    "2026-05-25",
    "2026-06-15",
    "2026-06-20",
    "2026-07-09"
]

# --- FECHAS ESPECIALES (2026) ---
DIA_DEL_PADRE   = "2026-06-21"  # Tercer domingo de junio
DIA_DE_LA_MADRE = "2026-10-18"  # Tercer domingo de octubre

# --- PERSONAL ---
# El personal se carga dinámicamente desde la base de datos
# según el SERVICIO_ID activo.
