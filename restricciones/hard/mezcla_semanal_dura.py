"""restricciones/hard/mezcla_semanal_dura.py — Prohíbe mezclar familias de turno en una misma semana."""
from restricciones.cargador import add_hard
from restricciones.hard._utils import determinar_familia_ganadora
from datetime import date, timedelta


def apply(modelo, ctx) -> None:
    if 'MEZCLA_SEMANAL_DURA' not in ctx.reglas_servicio:
        return
        
    fecha_inicio_dt = date.fromisoformat(ctx.fecha_inicio)
    dias_por_semana = {}
    for d in range(ctx.dias):
        fd = fecha_inicio_dt + timedelta(days=d)
        lunes = (fd - timedelta(days=fd.weekday())).isoformat()
        dias_por_semana.setdefault(lunes, []).append(d)

    primer_lunes_dt = fecha_inicio_dt - timedelta(days=fecha_inicio_dt.weekday())
    primer_lunes_key = primer_lunes_dt.isoformat()

    for emp in ctx.empleados:
        # 1. Aplicar la restricción del ganador del historial de la semana de transición (pasado)
        if primer_lunes_key in dias_por_semana:
            v_dict = ctx.vars_turno_sem.get((emp.nombre, primer_lunes_key))
            if v_dict:
                hist_prev = ctx.historial_semana_previa.get(emp.nombre, []) if ctx.historial_semana_previa else []
                ganador = determinar_familia_ganadora(hist_prev, primer_lunes_dt)
                if ganador and ganador in v_dict:
                    sid = primer_lunes_key.replace("-", "_")
                    add_hard(modelo, ctx,
                             modelo.Add(v_dict[ganador] == 1),
                             f"{emp.nombre}_hist_winner_{sid}_{ganador}")

        # 2. Evitar mezcla de turnos en la misma semana
        for sem_key in dias_por_semana:
            v_dict = ctx.vars_turno_sem.get((emp.nombre, sem_key))
            if v_dict:
                add_hard(modelo, ctx,
                         modelo.Add(v_dict['M'] + v_dict['T'] + v_dict['TN'] + v_dict['N'] <= 1),
                         f"{emp.nombre}_{sem_key}")
