"""restricciones/hard/mezcla_semanal_dura.py — Prohíbe mezclar familias de turno en una misma semana."""
from restricciones.cargador import add_hard
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

    for emp in ctx.empleados:
        for sem_key in dias_por_semana:
            v_dict = ctx.vars_turno_sem.get((emp.nombre, sem_key))
            if v_dict:
                add_hard(modelo, ctx,
                         modelo.Add(v_dict['M'] + v_dict['T'] + v_dict['TN'] + v_dict['N'] <= 1),
                         f"{emp.nombre}_{sem_key}")
