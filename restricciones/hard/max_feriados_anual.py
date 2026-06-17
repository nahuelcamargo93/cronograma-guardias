"""restricciones/hard/max_feriados_anual.py — Límite máximo estricto de feriados trabajados al año."""
from restricciones.cargador import add_hard
import rule_engine as _re

def apply(modelo, ctx) -> None:
    # 1. Verificar si la regla está configurada globalmente para el servicio
    if 'MAX_FERIADOS_ANUAL' not in ctx.reglas_servicio:
        return

    limite_global = ctx.reglas_servicio['MAX_FERIADOS_ANUAL'].get('max_feriados', 10)

    for emp in ctx.empleados:
        # Obtener parámetros para este empleado (por si se personaliza)
        params = _re.resolver_parametros_regla(
            'MAX_FERIADOS_ANUAL', emp.nombre, ctx.fecha_inicio,
            ctx.reglas_servicio, emp.reglas, ctx.ajustes_reglas_personal
        )
        if _re.regla_suspendida(params):
            continue

        limite = params.get('max_feriados', limite_global) if isinstance(params, dict) else limite_global

        # Evitar infeasibilidad si el histórico ya supera o iguala el límite
        cupo_restante = max(0, limite - emp.feriados_previos)

        # Buscar turnos en feriados asignables para este mes
        fer_vars = []
        for d in ctx.feriados:
            if d in emp.dias_licencia:
                continue
            for t in ctx.demanda_turnos.get('Finde_Feriado', {}).keys():
                if (emp.nombre, d, t) in ctx.turnos:
                    fer_vars.append(ctx.turnos[(emp.nombre, d, t)])

        if fer_vars:
            # Límite: Feriados asignados en el mes <= cupo restante
            add_hard(
                modelo, ctx,
                modelo.Add(sum(fer_vars) <= cupo_restante),
                f"{emp.nombre}_max_feriados"
            )
