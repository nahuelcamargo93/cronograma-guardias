"""restricciones/hard/franco_forzado.py — Prohíbe todos los turnos en días de franco administrativo."""
from datetime import date, timedelta
from restricciones.cargador import add_hard
from restricciones.hard._utils import prohibir_turnos_dia
import rule_engine as _re


def apply(modelo, ctx) -> None:
    fecha_inicio_dt = date.fromisoformat(ctx.fecha_inicio)
    for emp in ctx.empleados:
        for d in range(ctx.dias):
            if d in emp.dias_licencia:
                continue
            fecha_d_str = (fecha_inicio_dt + timedelta(days=d)).isoformat()
            params = _re.resolver_parametros_regla(
                'FRANCO_FORZADO', emp.nombre, fecha_d_str,
                ctx.reglas_servicio, emp.reglas, ctx.ajustes_reglas_personal
            )
            if _re.regla_existe(params) and not _re.regla_suspendida(params):
                prohibir_turnos_dia(modelo, ctx, emp.nombre, d)
