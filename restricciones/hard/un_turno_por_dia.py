"""restricciones/hard/un_turno_por_dia.py — Máximo un turno por persona por día."""
from datetime import date, timedelta
from restricciones.cargador import add_hard
import rule_engine as _re

_MAPA_DIAS = {"Lunes": 0, "Martes": 1, "Miercoles": 2, "Jueves": 3,
              "Viernes": 4, "Sabado": 5, "Domingo": 6}


def apply(modelo, ctx) -> None:
    fecha_inicio_dt = date.fromisoformat(ctx.fecha_inicio)
    for emp in ctx.empleados:
        for d in range(ctx.dias):
            td = "Finde_Feriado" if ((d + ctx.offset_dia) % 7 >= 5 or d in ctx.feriados) else "Semana"
            dia_semana = (d + ctx.offset_dia) % 7
            fecha_d = (fecha_inicio_dt + timedelta(days=d)).isoformat()

            fijos_hoy = 0
            params = _re.resolver_parametros_regla(
                'ASIGNACION_FIJA', emp.nombre, fecha_d,
                ctx.reglas_servicio, emp.reglas, ctx.ajustes_reglas_personal
            )
            if _re.regla_existe(params) and isinstance(params, list):
                for asig in params:
                    fecha_asig = asig.get('Fecha')
                    dia_asig   = asig.get('Dia')
                    if (fecha_asig and fecha_asig == fecha_d) or \
                       (dia_asig and _MAPA_DIAS.get(dia_asig) == dia_semana and d not in ctx.feriados):
                        fijos_hoy += 1

            max_t = max(1, fijos_hoy)
            todos = [ctx.turnos[(emp.nombre, d, t)]
                     for t in ctx.demanda_turnos.get(td, {}).keys()
                     if (emp.nombre, d, t) in ctx.turnos]
            if todos:
                add_hard(modelo, ctx,
                         modelo.Add(sum(todos) <= max_t),
                         f"{emp.nombre}_d{d}")
