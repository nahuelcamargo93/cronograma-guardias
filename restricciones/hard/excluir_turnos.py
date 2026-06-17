"""restricciones/hard/excluir_turnos.py — Prohíbe turnos específicos por día de semana."""
from datetime import date, timedelta
from restricciones.cargador import add_hard
import rule_engine as _re


def apply(modelo, ctx) -> None:
    fecha_inicio_dt = date.fromisoformat(ctx.fecha_inicio)
    for emp in ctx.empleados:
        for d in range(ctx.dias):
            fecha_d = (fecha_inicio_dt + timedelta(days=d)).isoformat()
            params = _re.resolver_parametros_regla(
                'EXCLUIR_TURNOS', emp.nombre, fecha_d,
                ctx.reglas_servicio, emp.reglas, ctx.ajustes_reglas_personal
            )
            if not _re.regla_existe(params) or not isinstance(params, list):
                continue
            dia_semana = (d + ctx.offset_dia) % 7
            for excl in params:
                if dia_semana not in excl.get('dias', list(range(7))):
                    continue
                for tp in excl.get('turnos', []):
                    if (emp.nombre, d, tp) in ctx.turnos:
                        add_hard(modelo, ctx,
                                 modelo.Add(ctx.turnos[(emp.nombre, d, tp)] == 0),
                                 f"{emp.nombre}_d{d}_{tp}")
