"""
restricciones/hard/finde_largo_reglamentario.py — DOUBLE (modo configurable HARD/SOFT)
Obliga o penaliza no otorgar el Fin de Semana Largo Reglamentario (4 días consecutivos).
Reglas: FINDE_LARGO_REGLAMENTARIO / FINDE_LARGO_REGLAMENTARIO_ESTRICTO
"""
from datetime import date, timedelta
from restricciones.cargador import add_hard
import rule_engine as _re

_PESO_INCUMPLE = 10_000


def apply(modelo, ctx):
    fecha_inicio_dt = date.fromisoformat(ctx.fecha_inicio)

    for emp in ctx.empleados:
        params = _re.resolver_parametros_regla(
            'FINDE_LARGO_REGLAMENTARIO', emp.nombre, ctx.fecha_inicio,
            ctx.reglas_servicio, emp.reglas, ctx.ajustes_reglas_personal
        )
        params_estricto = _re.resolver_parametros_regla(
            'FINDE_LARGO_REGLAMENTARIO_ESTRICTO', emp.nombre, ctx.fecha_inicio,
            ctx.reglas_servicio, emp.reglas, ctx.ajustes_reglas_personal
        )

        active = None
        if _re.regla_existe(params) and not _re.regla_suspendida(params):
            active = ('normal', params)
        elif _re.regla_existe(params_estricto) and not _re.regla_suspendida(params_estricto):
            active = ('estricto', params_estricto)
        if not active:
            continue

        tipo_regla, p = active
        modo = p.get('modo', 'HARD').upper() if isinstance(p, dict) else 'HARD'
        peso_soft = p.get('peso_soft', _PESO_INCUMPLE) if isinstance(p, dict) else _PESO_INCUMPLE
        flr_permitidos = p.get('flr_permitidos', ["jd", "sm"]) if isinstance(p, dict) else ["jd", "sm"]

        # 1. Agrupar findes por semana
        findes = {}
        for d in range(ctx.dias):
            wd = (fecha_inicio_dt + timedelta(days=d)).weekday()
            if wd in (5, 6):
                fd = fecha_inicio_dt + timedelta(days=d)
                lunes = (fd - timedelta(days=wd)).isoformat()
                findes.setdefault(lunes, []).append(d)

        # 2. Calcular disponibilidad (fines de semana donde al menos un día no está en licencias)
        k = sum(1 for _, dias in findes.items() if any(d not in emp.dias_licencia for d in dias))

        # 3. Determinar cantidad requerida basada en por_disponibilidad
        pd = p.get('por_disponibilidad')
        if isinstance(pd, dict):
            cantidad_req = pd.get(str(k), pd.get(k, 0))
        else:
            cantidad_req = 1 if k >= 3 else 0

        allowed_wds = []
        wd_map = {"jd": 3, "vl": 4, "sm": 5}
        for pref in flr_permitidos:
            if pref in wd_map:
                allowed_wds.append((wd_map[pref], pref))

        todas = []

        for d in range(ctx.dias):
            dia_sem = (d + ctx.offset_dia) % 7
            pref_activo = next((pref for wd, pref in allowed_wds if wd == dia_sem), None)
            if not pref_activo:
                continue
            if tipo_regla == 'estricto' and d + 3 >= ctx.dias:
                continue

            dias_obj = [d, d + 1, d + 2, d + 3]
            vars_bloque = []
            for d_e in dias_obj:
                if d_e >= ctx.dias:
                    if tipo_regla == 'estricto':
                        vars_bloque = []
                        break
                    continue
                if d_e in emp.dias_licencia:
                    vars_bloque = []
                    break
                es_f_e = ((d_e + ctx.offset_dia) % 7 >= 5) or (d_e in ctx.feriados)
                tipo_d = 'Finde_Feriado' if es_f_e else 'Semana'
                for t in ctx.demanda_turnos.get(tipo_d, {}).keys():
                    if (emp.nombre, d_e, t) in ctx.turnos:
                        vars_bloque.append(ctx.turnos[(emp.nombre, d_e, t)])

            if not vars_bloque:
                continue

            tipo_str = pref_activo
            tiene_flr = modelo.NewBoolVar(f'flr_{tipo_str}_{emp.nombre}_d{d}')
            
            conds_flr = []
            
            libre = modelo.NewBoolVar(f'libre_{tipo_str}_{emp.nombre}_d{d}')
            modelo.Add(sum(vars_bloque) == 0).OnlyEnforceIf(libre)
            modelo.Add(sum(vars_bloque) > 0).OnlyEnforceIf(libre.Not())
            conds_flr.append(libre)

            # Restricción adyacente: si tiene FLR, trabaja el día anterior y posterior
            if d - 1 >= 0:
                es_f_p = ((d - 1 + ctx.offset_dia) % 7 >= 5) or (d - 1 in ctx.feriados)
                vars_prev = [
                    ctx.turnos[(emp.nombre, d - 1, t)]
                    for t in ctx.demanda_turnos.get(
                        'Finde_Feriado' if es_f_p else 'Semana', {}
                    ).keys()
                    if (emp.nombre, d - 1, t) in ctx.turnos
                ]
                if vars_prev:
                    prev_ok = modelo.NewBoolVar(f'prev_ok_{tipo_str}_{emp.nombre}_d{d}')
                    modelo.Add(sum(vars_prev) == 1).OnlyEnforceIf(prev_ok)
                    modelo.Add(sum(vars_prev) != 1).OnlyEnforceIf(prev_ok.Not())
                    conds_flr.append(prev_ok)
                else:
                    conds_flr.append(modelo.NewConstant(0))
            else:
                conds_flr.append(modelo.NewConstant(0))

            if d + 4 < ctx.dias:
                es_f_po = ((d + 4 + ctx.offset_dia) % 7 >= 5) or (d + 4 in ctx.feriados)
                vars_post = [
                    ctx.turnos[(emp.nombre, d + 4, t)]
                    for t in ctx.demanda_turnos.get(
                        'Finde_Feriado' if es_f_po else 'Semana', {}
                    ).keys()
                    if (emp.nombre, d + 4, t) in ctx.turnos
                ]
                if vars_post:
                    post_ok = modelo.NewBoolVar(f'post_ok_{tipo_str}_{emp.nombre}_d{d}')
                    modelo.Add(sum(vars_post) == 1).OnlyEnforceIf(post_ok)
                    modelo.Add(sum(vars_post) != 1).OnlyEnforceIf(post_ok.Not())
                    conds_flr.append(post_ok)
                else:
                    conds_flr.append(modelo.NewConstant(0))
            else:
                conds_flr.append(modelo.NewConstant(0))

            modelo.AddMinEquality(tiene_flr, conds_flr)

            todas.append(tiene_flr)
            
            # Penalidades específicas
            if pref_activo == "jd":
                ctx.penalizaciones_soft.append(tiene_flr * 3000)
            elif pref_activo == "vl":
                ctx.penalizaciones_soft.append(tiene_flr * 1000)

            if ctx.flr_tracker is not None:
                ctx.flr_tracker[(emp.nombre, d)] = tiene_flr

        if todas and cantidad_req > 0:
            if modo == 'HARD':
                add_hard(modelo, ctx,
                         modelo.Add(sum(todas) >= cantidad_req),
                         f"{emp.nombre}_cantidad")
            else:  # SOFT
                incumple = modelo.NewIntVar(0, cantidad_req, f'incumple_flr_{emp.nombre}')
                modelo.Add(sum(todas) + incumple == cantidad_req)
                ctx.penalizaciones_soft.append(incumple * peso_soft)
