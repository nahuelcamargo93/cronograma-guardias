"""
restricciones/hard/ — Leyes físicas del cronograma.

Restricciones que bajo ninguna circunstancia se pueden flexibilizar
porque romperían la lógica elemental del sistema.

Ejemplos: UN_TURNO_POR_DIA, LICENCIAS, EXCLUIR_TURNOS,
          DESCANSO_ENTRE_TURNOS, PATRON_CICLICO.

Cada archivo en este directorio implementa UNA sola regla
y expone la función:

    def apply(modelo, ctx) -> None

Nota: _utils.py es un módulo de utilidades compartidas, NO es una regla.
Las reglas marcadas con [D] son conceptualmente double pero se ejecutan
como hard con soporte de add_hard (MODO_DEBUG las convierte en soft).
"""

# Registro ordenado de reglas para el cargador dinámico (Tarea 2.5).
# El orden importa: las reglas más fundamentales van primero.
REGLAS_HARD = [
    # 1. Bloqueos absolutos (deben ir antes que cualquier otra regla)
    "restricciones.hard.licencias",
    "restricciones.hard.franco_forzado",
    "restricciones.hard.excluir_turnos",
    "restricciones.hard.fechas_especiales",
    "restricciones.hard.puestos_solo_fijos",
    "restricciones.hard.solo_asignaciones_fijas",
    "restricciones.hard.asignacion_fija_obligatoria",

    # 2. Cobertura y demanda (el motor depende de estas para ser feasible)
    "restricciones.hard.cobertura_dinamica",

    # 3. Estructura de la semana
    "restricciones.hard.un_turno_por_dia",
    "restricciones.hard.mezcla_semanal_dura",
    "restricciones.hard.no_repetir_turno_consecutivo",
    "restricciones.hard.esquema_semanal_enfermeria",
    "restricciones.hard.balance_dia_noche",

    # 4. Restricciones de licencias y patrones
    "restricciones.hard.fin_licencia",
    "restricciones.hard.finde_post_licencia",
    "restricciones.hard.franco_previo_lpp",
    "restricciones.hard.turno_previo_licencia",
    "restricciones.hard.patron_ciclico",
    "restricciones.hard.personal_asociado",
    "restricciones.hard.personal_disociado",
    "restricciones.hard.rotacion_mensual_dura",
    "restricciones.hard.max_feriados_anual",
    "restricciones.hard.semanas_seguimiento_requeridas",
    "restricciones.hard.orden_rotacion_semanal",
]
