"""restricciones/hard/no_repetir_turno_consecutivo.py — Prohíbe repetir el mismo tipo de turno semanal en semanas consecutivas."""
from restricciones.cargador import add_hard
from datetime import date, timedelta
from restricciones.hard._utils import determinar_familia_ganadora


def apply(modelo, ctx) -> None:
    if 'NO_REPETIR_TURNO_CONSECUTIVO' not in ctx.reglas_servicio:
        return

    fecha_inicio_dt = date.fromisoformat(ctx.fecha_inicio)
    dias_por_semana = {}
    for d in range(ctx.dias):
        fd = fecha_inicio_dt + timedelta(days=d)
        lunes = (fd - timedelta(days=fd.weekday())).isoformat()
        dias_por_semana.setdefault(lunes, []).append(d)

    semanas_keys = sorted(dias_por_semana.keys())
    if not semanas_keys:
        return

    primer_lunes = date.fromisoformat(semanas_keys[0])

    for emp in ctx.empleados:
        nombre = emp.nombre
        hist_prev = ctx.historial_semana_previa.get(nombre, []) if ctx.historial_semana_previa else []

        # 1. Chequear transición con la semana previa a la planificación
        ganador_prev = determinar_familia_ganadora(hist_prev, primer_lunes - timedelta(days=7))
        ganador_primera = determinar_familia_ganadora(hist_prev, primer_lunes)

        if ganador_prev and (ganador_primera is None):
            # Evitar el mismo turno en la primera semana planificada
            v_dict_first = ctx.vars_turno_sem.get((nombre, semanas_keys[0]))
            if v_dict_first and ganador_prev in v_dict_first:
                add_hard(modelo, ctx,
                         modelo.Add(v_dict_first[ganador_prev] == 0),
                         f"{nombre}_prev_to_{semanas_keys[0]}_{ganador_prev}")

        # 2. Restricción entre semanas del mes planificado
        for idx in range(len(semanas_keys) - 1):
            sem_actual = semanas_keys[idx]
            sem_siguiente = semanas_keys[idx + 1]

            v_dict_act = ctx.vars_turno_sem.get((nombre, sem_actual))
            v_dict_sig = ctx.vars_turno_sem.get((nombre, sem_siguiente))

            if v_dict_act and v_dict_sig:
                for k in ['M', 'T', 'TN', 'N']:
                    if k in v_dict_act and k in v_dict_sig:
                        add_hard(modelo, ctx,
                                 modelo.Add(v_dict_act[k] + v_dict_sig[k] <= 1),
                                 f"{nombre}_{sem_actual}_{sem_siguiente}_{k}")
