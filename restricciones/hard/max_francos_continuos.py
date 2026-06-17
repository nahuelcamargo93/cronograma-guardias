"""restricciones/hard/max_francos_continuos.py — Límite máximo de francos consecutivos.

Esta regla asegura que ningún profesional tenga más de la cantidad máxima de
francos seguidos configurada en el mes, contemplando la transición del
historial de la semana previa. Los días de licencia se consideran como no
francos para evitar que causen inviabilidades.
"""
from datetime import date, timedelta
from restricciones.cargador import add_hard
from restricciones.hard._utils import is_finde
import rule_engine as _re


def apply(modelo, ctx) -> None:
    fecha_inicio_dt = date.fromisoformat(ctx.fecha_inicio)
    historial = ctx.historial_semana_previa or {}

    for emp in ctx.empleados:
        params = _re.resolver_parametros_regla(
            'MAX_FRANCOS_CONTINUOS', emp.nombre, ctx.fecha_inicio,
            ctx.reglas_servicio, emp.reglas, ctx.ajustes_reglas_personal
        )
        if _re.regla_suspendida(params):
            continue

        max_francos = params.get('max_francos') if isinstance(params, dict) else None
        if not max_francos or max_francos <= 0:
            continue

        modo = params.get('modo', 'HARD').upper() if isinstance(params, dict) else 'HARD'
        peso_soft = params.get('peso_soft', 10000) if isinstance(params, dict) else 10000

        # Determinar si el empleado trabaja cada día del mes
        traba_dia = {}
        for d in range(ctx.dias):
            td = "Finde_Feriado" if is_finde(d, ctx.offset_dia, ctx.feriados) else "Semana"
            t_dia = [ctx.turnos[(emp.nombre, d, t)]
                     for t in ctx.demanda_turnos.get(td, {}).keys()
                     if (emp.nombre, d, t) in ctx.turnos]
            if t_dia:
                v = modelo.NewBoolVar(f"traba_dia_{emp.nombre}_d{d}")
                modelo.Add(v == sum(t_dia))
                traba_dia[d] = v
            else:
                traba_dia[d] = 0

        # Construir variable de franco F[d]
        F = {}
        for d in range(ctx.dias):
            es_lic = 1 if d in emp.dias_licencia else 0
            v_franco = modelo.NewBoolVar(f"franco_{emp.nombre}_d{d}")
            # F[d] = 1 - traba_dia[d] - es_licencia
            # O sea: F[d] + traba_dia[d] + es_licencia == 1. Pero traba_dia[d] puede ser 0 o BoolVar.
            # Usamos modelo.Add(v_franco == 1 - traba_dia[d] - es_lic) que es linealmente equivalente a:
            modelo.Add(v_franco + traba_dia[d] + es_lic == 1)
            F[d] = v_franco

        # Incorporar el historial previo
        hist_emp = historial.get(emp.nombre, [])
        worked_hist = {h['fecha'] for h in hist_emp}
        
        T = {}
        for d in range(-max_francos, ctx.dias):
            if d < 0:
                fecha_h = (fecha_inicio_dt + timedelta(days=d)).strftime("%Y-%m-%d")
                # Si no hay historial previo para este empleado, asumimos que no fue franco (0) para evitar inviabilidades
                if not worked_hist:
                    T[d] = 0
                else:
                    T[d] = 0 if fecha_h in worked_hist else 1
            else:
                T[d] = F[d]

        window = max_francos + 1
        for start in range(-max_francos, ctx.dias - max_francos):
            win = [T[d] for d in range(start, start + window)]
            
            if modo == 'HARD':
                ct = modelo.Add(sum(win) <= max_francos)
                add_hard(modelo, ctx, ct, f"{emp.nombre}_w{start}")
            else:  # SOFT
                v_viol = modelo.NewBoolVar(f"viol_max_fr_cont_{emp.nombre}_w{start}")
                modelo.Add(sum(win) <= max_francos + v_viol)
                ctx.penalizaciones_soft.append(v_viol * peso_soft)
