"""restricciones/hard/fechas_especiales.py — Franco obligatorio en cumpleaños y día del padre/madre."""
from datetime import date, timedelta
from restricciones.hard._utils import prohibir_turnos_dia
import rule_engine as _re


def apply(modelo, ctx) -> None:
    fecha_inicio_dt = date.fromisoformat(ctx.fecha_inicio)
    for emp in ctx.empleados:
        for d in range(ctx.dias):
            fecha_d_dt = fecha_inicio_dt + timedelta(days=d)
            fecha_d_str = fecha_d_dt.isoformat()

            # 1. Cumpleaños
            p_cumple = _re.resolver_parametros_regla(
                'CUMPLEANOS_LIBRE', emp.nombre, fecha_d_str,
                ctx.reglas_servicio, emp.reglas, ctx.ajustes_reglas_personal
            )
            if _re.regla_existe(p_cumple) and not _re.regla_suspendida(p_cumple):
                if emp.fecha_cumpleanos and isinstance(emp.fecha_cumpleanos, str):
                    match = False
                    try:
                        fc = date.fromisoformat(emp.fecha_cumpleanos)
                        match = (fc.month == fecha_d_dt.month and fc.day == fecha_d_dt.day)
                    except ValueError:
                        if len(emp.fecha_cumpleanos) == 5 and emp.fecha_cumpleanos[2] == '-':
                            match = (emp.fecha_cumpleanos == f"{fecha_d_dt.month:02d}-{fecha_d_dt.day:02d}")
                    if match:
                        prohibir_turnos_dia(modelo, ctx, emp.nombre, d)

            # 2. Día del padre / madre
            p_familia = _re.resolver_parametros_regla(
                'DIA_MADRE_PADRE_LIBRE', emp.nombre, fecha_d_str,
                ctx.reglas_servicio, emp.reglas, ctx.ajustes_reglas_personal
            )
            if _re.regla_existe(p_familia) and not _re.regla_suspendida(p_familia):
                # Calcular dinámicamente el día del padre (3er domingo de junio) y de la madre (3er domingo de octubre)
                anio = fecha_d_dt.year
                
                # Día del Padre: 3er domingo de junio
                primer_dia_junio = date(anio, 6, 1)
                dia_padre_dt = primer_dia_junio + timedelta(days=((6 - primer_dia_junio.weekday()) % 7) + 14)
                
                # Día de la Madre: 3er domingo de octubre
                primer_dia_octubre = date(anio, 10, 1)
                dia_madre_dt = primer_dia_octubre + timedelta(days=((6 - primer_dia_octubre.weekday()) % 7) + 14)
                
                if emp.es_padre and fecha_d_dt == dia_padre_dt:
                    prohibir_turnos_dia(modelo, ctx, emp.nombre, d)
                if emp.es_madre and fecha_d_dt == dia_madre_dt:
                    prohibir_turnos_dia(modelo, ctx, emp.nombre, d)

