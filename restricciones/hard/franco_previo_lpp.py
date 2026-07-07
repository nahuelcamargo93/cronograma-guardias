"""restricciones/hard/franco_previo_lpp.py — Obliga a dar franco el fin de semana previo al inicio de una licencia LPP (si inicia un lunes)."""
from datetime import date
from restricciones.cargador import add_hard
from restricciones.hard._utils import es_finde_previo_lpp


def apply(modelo, ctx) -> None:
    fecha_inicio_dt = date.fromisoformat(ctx.fecha_inicio)

    for emp in ctx.empleados:
        for d in range(ctx.dias):
            if es_finde_previo_lpp(emp, d, fecha_inicio_dt):
                # Forzar que todas las variables de turno para este día sean 0 (franco obligatorio)
                for td in ["Semana", "Finde_Feriado"]:
                    for t in ctx.demanda_turnos.get(td, {}).keys():
                        key = (emp.nombre, d, t)
                        if key in ctx.turnos:
                            add_hard(modelo, ctx,
                                     modelo.Add(ctx.turnos[key] == 0),
                                     f"{emp.nombre}_lpp_prev_fs_d{d}")
