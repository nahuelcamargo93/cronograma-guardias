"""
restricciones/double/ — Límites y reglas paramétricas (modo configurable).

Restricciones institucionales cuyo comportamiento se determina en tiempo
de ejecución leyendo el campo 'modo' del JSON almacenado en la DB:

  modo = "HARD"  → actúa como restricción dura (bloquea soluciones)
  modo = "SOFT"  → actúa como penalización en la función objetivo
                   usando el campo 'peso_soft' del mismo JSON.

Cada archivo en este directorio implementa UNA sola regla
y expone la función:

    def apply(modelo, ctx) -> None

La función es responsable de leer ctx.params['modo'] y bifurcar
su comportamiento entre HARD y SOFT internamente.

Nota: Las siguientes reglas están físicamente en /hard porque su
implementación actual las trata como hard con soporte de debugger
(add_hard), pero conceptualmente son dobles:
  - exacto_finde_y_dia.py       (modo_filtro HARD/SOFT)
  - finds_completos_y_medios.py
  - exacto_dia_especifico_mes.py
  - min_finds_mes.py
  - max_horas_mes_calendario.py
  - min_horas_mes_calendario.py
  - max_horas_semana.py
  - max_dias_continuos.py
  - max_turnos.py / min_turnos.py
"""

# Registro de reglas dobles (usadas por el cargador dinámico Tarea 2.5)
REGLAS_DOUBLE = [
    "restricciones.hard.exacto_finde_y_dia",
    "restricciones.hard.finds_completos_y_medios",
    "restricciones.hard.exacto_dia_especifico_mes",
    "restricciones.hard.min_findes_mes",
    "restricciones.hard.max_horas_mes_calendario",
    "restricciones.hard.min_horas_mes_calendario",
    "restricciones.hard.max_horas_semana",
    "restricciones.hard.min_horas_semana",
    "restricciones.hard.max_dias_continuos",
    "restricciones.hard.max_turnos",
    "restricciones.hard.min_turnos",
    "restricciones.hard.finde_largo_reglamentario",
    "restricciones.hard.brecha_diaria_personal",
    "restricciones.hard.descanso_entre_turnos",
    "restricciones.hard.max_francos_semana",
    "restricciones.hard.max_francos_continuos",
    "restricciones.hard.min_turnos_semana",
    "restricciones.hard.min_francos_semana",
    "restricciones.double.manejo_findes",
    "restricciones.double.no_repetir_n_consecutivo",
    "restricciones.double.repeticion_tipo_semana",
]
