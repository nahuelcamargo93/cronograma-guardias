"""restricciones/hard/licencias.py — Bloquea todos los turnos en días de licencia formal."""
from restricciones.cargador import add_hard


def apply(modelo, ctx) -> None:
    for emp in ctx.empleados:
        for d in emp.dias_licencia:
            for td in ["Semana", "Finde_Feriado"]:
                for t in ctx.demanda_turnos.get(td, {}).keys():
                    if (emp.nombre, d, t) in ctx.turnos:
                        add_hard(modelo, ctx,
                                 modelo.Add(ctx.turnos[(emp.nombre, d, t)] == 0),
                                 f"{emp.nombre}_d{d}")
