"""restricciones/hard/finds_completos_y_medios.py — Cantidad exacta de fines completos y medios."""
from datetime import date, timedelta
from restricciones.cargador import add_hard
import rule_engine as _re


def apply(modelo, ctx) -> None:
    fecha_inicio_dt = date.fromisoformat(ctx.fecha_inicio)
    ref_fecha = ctx.fecha_inicio

    for emp in ctx.empleados:
        params = _re.resolver_parametros_regla(
            'FINDES_COMPLETOS_Y_MEDIOS', emp.nombre, ref_fecha,
            ctx.reglas_servicio, emp.reglas, ctx.ajustes_reglas_personal
        )
        if not _re.regla_existe(params) or _re.regla_suspendida(params): continue

        # Agrupar sábado y domingo por semana
        findes = {}
        for d in range(ctx.dias):
            wd = (fecha_inicio_dt + timedelta(days=d)).weekday()
            if wd in (5, 6):
                fd = fecha_inicio_dt + timedelta(days=d)
                lunes = (fd - timedelta(days=wd)).isoformat()
                findes.setdefault(lunes, []).append((d, wd))

        def _disponible(d):
            if d in emp.dias_licencia: return False
            p = _re.resolver_parametros_regla(
                'FRANCO_FORZADO', emp.nombre,
                (fecha_inicio_dt + timedelta(days=d)).isoformat(),
                ctx.reglas_servicio, emp.reglas, ctx.ajustes_reglas_personal
            )
            return not (_re.regla_existe(p) and not _re.regla_suspendida(p))

        k = sum(1 for _, dias_f in findes.items() if any(_disponible(d) for d, _ in dias_f))
        conf = params.get('por_disponibilidad', {}).get(str(k))
        if not conf:
            conf = {5: {"completos": 3, "medios": 1}, 4: {"completos": 2, "medios": 1},
                    3: {"completos": 1, "medios": 1}, 2: {"completos": 1, "medios": 0},
                    1: {"completos": 0, "medios": 1}}.get(k, {"completos": 0, "medios": 0})

        target_c = conf.get('completos', 0)
        target_m = conf.get('medios', 0)
        posibles_c = posibles_m = 0
        vars_completo, vars_medio = [], []

        for lunes, dias_f in findes.items():
            d_sat = next((d for d, w in dias_f if w == 5), None)
            d_sun = next((d for d, w in dias_f if w == 6), None)
            if d_sat is None or d_sun is None: continue

            sat_ok = _disponible(d_sat)
            sun_ok = _disponible(d_sun)
            if sat_ok and sun_ok: posibles_c += 1
            if sat_ok or sun_ok: posibles_m += 1

            pool_sat = [ctx.turnos[(emp.nombre, d_sat, t)]
                        for t in ctx.demanda_turnos.get("Finde_Feriado", {}).keys()
                        if (emp.nombre, d_sat, t) in ctx.turnos]
            v_sat = modelo.NewBoolVar(f'sat_{emp.nombre}_{lunes}')
            if pool_sat: modelo.AddMaxEquality(v_sat, pool_sat)
            else: modelo.Add(v_sat == 0)

            pool_sun = [ctx.turnos[(emp.nombre, d_sun, t)]
                        for t in ctx.demanda_turnos.get("Finde_Feriado", {}).keys()
                        if (emp.nombre, d_sun, t) in ctx.turnos]
            v_sun = modelo.NewBoolVar(f'sun_{emp.nombre}_{lunes}')
            if pool_sun: modelo.AddMaxEquality(v_sun, pool_sun)
            else: modelo.Add(v_sun == 0)

            v_comp = modelo.NewBoolVar(f'f_comp_{emp.nombre}_{lunes}')
            modelo.AddMinEquality(v_comp, [v_sat, v_sun])
            vars_completo.append(v_comp)

            v_med = modelo.NewBoolVar(f'f_med_{emp.nombre}_{lunes}')
            modelo.Add(v_sat + v_sun - 2 * v_comp == v_med)
            vars_medio.append(v_med)

        target_c_real = min(target_c, posibles_c)
        target_m_real = min(target_m, posibles_m - target_c_real)
        if vars_completo:
            add_hard(modelo, ctx, modelo.Add(sum(vars_completo) == target_c_real), f"{emp.nombre}_compl")
        if vars_medio:
            add_hard(modelo, ctx, modelo.Add(sum(vars_medio) == target_m_real), f"{emp.nombre}_medio")
