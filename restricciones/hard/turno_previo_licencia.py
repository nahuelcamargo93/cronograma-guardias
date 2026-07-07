"""restricciones/hard/turno_previo_licencia.py — Prohíbe un tipo de turno el día previo al inicio de una licencia."""
from restricciones.cargador import add_hard
import rule_engine as _re


def apply(modelo, ctx) -> None:
    ref_fecha = ctx.fecha_inicio

    for emp in ctx.empleados:
        p_prev = _re.resolver_parametros_regla(
            'TURNO_PREVIO_LICENCIA', emp.nombre, ref_fecha, ctx.reglas_servicio, emp.reglas, ctx.ajustes_reglas_personal
        )
        if not _re.regla_existe(p_prev) or _re.regla_suspendida(p_prev):
            continue

        # Obtener turnos prohibidos
        turnos_prohibidos = p_prev.get('turnos', [])
        if isinstance(turnos_prohibidos, str):
            turnos_prohibidos = [turnos_prohibidos]
        
        # También soportar 'turno' en singular
        if 'turno' in p_prev:
            t_sing = p_prev['turno']
            if t_sing not in turnos_prohibidos:
                turnos_prohibidos.append(t_sing)

        if not turnos_prohibidos:
            continue

        from datetime import date, timedelta
        fecha_inicio_dt = date.fromisoformat(ctx.fecha_inicio)

        for d in range(ctx.dias):
            if d in emp.dias_licencia and (d == 0 or (d - 1) not in emp.dias_licencia):
                tipo_lic = getattr(emp, 'tipos_licencia', {}).get(d)
                
                fecha_d = fecha_inicio_dt + timedelta(days=d)
                if tipo_lic == 'LPP' and fecha_d.weekday() == 0:
                    dia_target = d - 3  # Viernes previo
                else:
                    dia_target = d - 1  # Día previo estándar
                
                if 0 <= dia_target < ctx.dias:
                    for t in turnos_prohibidos:
                        key = (emp.nombre, dia_target, t)
                        if key in ctx.turnos:
                            add_hard(modelo, ctx,
                                     modelo.Add(ctx.turnos[key] == 0),
                                     f"{emp.nombre}_prev_lic_{tipo_lic or 'GEN'}_d{dia_target}_{t}")
