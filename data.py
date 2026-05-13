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
# Solo Nombre y Rol. Todas las demás propiedades (prohibiciones,
# seguimientos, asignaciones fijas, límites, vacantes) se
# configuran en la base de datos.
PERSONAL = [
    {'Nombre': 'ABELENDA GRISELL', 'Rol': 'Rotativo'},
    {'Nombre': 'ALBELO TANIA', 'Rol': 'Rotativo'},
    {'Nombre': 'ALCARAZ ELIANA', 'Rol': 'Rotativo'},
    {'Nombre': 'ALCARAZ FRANCISO', 'Rol': 'Rotativo'},
    {'Nombre': 'ANDREOLI LUCIANA', 'Rol': 'Rotativo'},
    {'Nombre': 'ARCE DANIEL', 'Rol': 'Rotativo'},
    {'Nombre': 'ASTUDILLO MELINA', 'Rol': 'Rotativo'},
    {'Nombre': 'BARROSO ERICA', 'Rol': 'Rotativo'},
    {'Nombre': 'BASCUR ALEJANDRA', 'Rol': 'Rotativo'},
    {'Nombre': 'BORIA MAYRA', 'Rol': 'Rotativo'},
    {'Nombre': 'CALDERON MARIA JOSE', 'Rol': 'Rotativo'},
    {'Nombre': 'CAMPOS PRISCILA', 'Rol': 'Rotativo'},
    {'Nombre': 'CARRERAS FLAVIA', 'Rol': 'Rotativo'},
    {'Nombre': 'CASTRO LUCIANO', 'Rol': 'Rotativo'},
    {'Nombre': 'CORSO ARTURO', 'Rol': 'Rotativo'},
    {'Nombre': 'CHIRINO CAROLINA', 'Rol': 'Rotativo'},
    {'Nombre': 'CORIA LUCIANO', 'Rol': 'Rotativo'},
    {'Nombre': 'DOMINGUEZ VERONICA', 'Rol': 'Rotativo'},
    {'Nombre': 'DURAN JAZMIN', 'Rol': 'Rotativo'},
    {'Nombre': 'ECHENIQUE ROCIO', 'Rol': 'Rotativo'},
    {'Nombre': 'ESCALANTE CARLA', 'Rol': 'Rotativo'},
    {'Nombre': 'ESCUDERO SERGIO', 'Rol': 'Rotativo'},
    {'Nombre': 'FERNANDEZ PAOLA', 'Rol': 'Rotativo'},
    {'Nombre': 'FERNANDEZ YESICA', 'Rol': 'Rotativo'},
    {'Nombre': 'GIMENEZ KAREN', 'Rol': 'Rotativo'},
    {'Nombre': 'GOMES STHEFANIA', 'Rol': 'Rotativo'},
    {'Nombre': 'GOMEZ LOURDES', 'Rol': 'Rotativo'},
    {'Nombre': 'GRABOVIECKI FERNANDA', 'Rol': 'Rotativo'},
    {'Nombre': 'GUIAZU KARINA', 'Rol': 'Rotativo'},
    {'Nombre': 'IRAZABAL MARIANGELES', 'Rol': 'Rotativo'},
    {'Nombre': 'LUCERO MATIAS', 'Rol': 'Rotativo'},
    {'Nombre': 'MAE LORENA', 'Rol': 'Rotativo'},
    {'Nombre': 'MEDINA LAURA', 'Rol': 'Rotativo'},
    {'Nombre': 'MIRANDA LUCIANA', 'Rol': 'Rotativo'},
    {'Nombre': 'MIRANDA YANINA', 'Rol': 'Rotativo'},
    {'Nombre': 'MONDONE PAULA', 'Rol': 'Rotativo'},
    {'Nombre': 'NIEVAS CARLA', 'Rol': 'Rotativo'},
    {'Nombre': 'OLGUIN LUCIA', 'Rol': 'Rotativo'},
    {'Nombre': 'ORTIZ LAURA', 'Rol': 'Rotativo'},
    {'Nombre': 'PALACIOS FACUNDO', 'Rol': 'Rotativo'},
    {'Nombre': 'PALANA GRACIELA', 'Rol': 'Rotativo'},
    {'Nombre': 'PEREIRA CRISTINA', 'Rol': 'Rotativo'},
    {'Nombre': 'POLETTI NATALIA', 'Rol': 'Rotativo'},
    {'Nombre': 'QUEVEDO CELESTE', 'Rol': 'Rotativo'},
    {'Nombre': 'RINALDINI IVANA', 'Rol': 'Rotativo'},
    {'Nombre': 'ROJAS JULIANA', 'Rol': 'Rotativo'},
    {'Nombre': 'SOSA NAHUEL', 'Rol': 'Rotativo'},
    {'Nombre': 'SUAREZ JESICA', 'Rol': 'Rotativo'},
    {'Nombre': 'TULA DAIANA', 'Rol': 'Rotativo'},
    {'Nombre': 'VELEZ DANIEL', 'Rol': 'Rotativo'},
    {'Nombre': 'VELIZ LIONEL', 'Rol': 'Rotativo'},
    {'Nombre': 'VERA JULIETA', 'Rol': 'Rotativo'},
]

# --- HELPERS ---
def asignar_horas(turno):
    """Devuelve las horas de un turno por su nombre."""
    if turno.startswith("Noche") or turno.startswith("Dia"):
        return 12
    return 6
